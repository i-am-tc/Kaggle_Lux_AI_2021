from omegaconf import OmegaConf
from pathlib import Path
import torch
from torch import nn
from typing import *

from ..lux_gym.obs_spaces import MAX_BOARD_SIZE
from .models import BasicActorCriticNetwork
from .in_blocks import ConvEmbeddingInputLayer
from .attn_blocks import ViTBlock
from .conv_blocks import FullConvResidualBlock


def create_model(flags, device: torch.device) -> nn.Module:
    if flags.model_arch == "dummy_conv_model":
        base_model = nn.Sequential(
            ConvEmbeddingInputLayer(
                obs_space=flags.obs_space.get_obs_spec(),
                embedding_dim=flags.hidden_dim,
                use_index_select=flags.use_index_select
            ),
            FullConvResidualBlock(
                in_channels=flags.hidden_dim,
                out_channels=flags.hidden_dim,
                height=MAX_BOARD_SIZE[0],
                width=MAX_BOARD_SIZE[1],
                kernel_size=3,
                normalize=flags.normalize,
            ),
            FullConvResidualBlock(
                in_channels=flags.hidden_dim,
                out_channels=flags.hidden_dim,
                height=MAX_BOARD_SIZE[0],
                width=MAX_BOARD_SIZE[1],
                kernel_size=3,
                normalize=flags.normalize,
            ),
        )
        model = BasicActorCriticNetwork(
            base_model=base_model,
            base_out_channels=flags.hidden_dim,
            action_space=flags.act_space.get_action_space(),
            reward_space=flags.reward_space.get_reward_spec(),
        )
    elif flags.model_arch == "dummy_attention_model":
        base_model = nn.Sequential(
            ConvEmbeddingInputLayer(
                obs_space=flags.obs_space.get_obs_spec(),
                embedding_dim=flags.hidden_dim,
                use_index_select=flags.use_index_select
            ),
            ViTBlock(
                in_channels=flags.hidden_dim,
                out_channels=flags.hidden_dim,
                mhsa_heads=4,
                height=MAX_BOARD_SIZE[0],
                width=MAX_BOARD_SIZE[1],
                normalize=flags.normalize
            ),
            ViTBlock(
                in_channels=flags.hidden_dim,
                out_channels=flags.hidden_dim,
                mhsa_heads=4,
                height=MAX_BOARD_SIZE[0],
                width=MAX_BOARD_SIZE[1],
                normalize=flags.normalize
            ),
        )
        model = BasicActorCriticNetwork(
            base_model=base_model,
            base_out_channels=flags.hidden_dim,
            action_space=flags.act_space.get_action_space(),
            reward_space=flags.reward_space.get_reward_spec(),
        )
    elif flags.model_arch == "attention_model":
        base_model = nn.Sequential(
            ConvEmbeddingInputLayer(
                obs_space=flags.obs_space.get_obs_spec(),
                embedding_dim=flags.hidden_dim,
                use_index_select=flags.use_index_select
            ),
            *[ViTBlock(
                in_channels=flags.hidden_dim,
                out_channels=flags.hidden_dim,
                mhsa_heads=4,
                height=MAX_BOARD_SIZE[0],
                width=MAX_BOARD_SIZE[1],
                normalize=flags.normalize
            ) for _ in range(flags.n_blocks)]
        )
        model = BasicActorCriticNetwork(
            base_model=base_model,
            base_out_channels=flags.hidden_dim,
            action_space=flags.act_space.get_action_space(),
            reward_space=flags.reward_space.get_reward_spec(),
        )
    else:
        raise NotImplementedError(f"Model_arch: {flags.model_arch}")

    model.to(device=device)
    return model


def load_model(load_dir: Union[Path, str], model_checkpoint: str, device: torch.device):
    flags = OmegaConf.load(load_dir + "/config.yaml")
    flags.checkpoint = Path(load_dir) / (model_checkpoint + ".pt")
    model = create_model(flags, device)
    print(flags.checkpoint)
    checkpoint_states = torch.load(flags.checkpoint, map_location=device)
    model.load_state_dict(checkpoint_states["model_state_dict"])
    return model
