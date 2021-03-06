import argparse
import importlib
from sys import stderr

import gym
from loguru import logger

import gym_minigrid  # noqa
from purls.algorithms import modules, AlgorithmError
from purls.algorithms.base import ReinforcementLearningAlgorithm
from purls.utils.logs import debug, error, get_format, info

for module in modules:
    importlib.import_module(module)


def run(action, args):
    algorithms = {}
    debug("algorithms detected:")
    for algorithm in ReinforcementLearningAlgorithm.subclasses:
        debug(algorithm.__name__)
        algorithms.update({algorithm.__name__: algorithm})
    debug("")

    try:
        if args.algorithm not in algorithms:
            valid_algorithms = ", ".join(algorithms.keys())
            error(f"choose a valid algorithm: {valid_algorithms}")
            return 1
        try:
            env = gym.make(args.environment)
        except gym.error.Error:
            valid_environments = "\n".join(
                [env.id for env in gym.envs.registry.all() if env.id.startswith("MiniGrid")]
            )
            error(f"choose a valid gym enviroment:\n{valid_environments}")
            return 1

        algo = algorithms[args.algorithm](env=env, args=args)
        with logger.catch(reraise=True):
            if action == "train":
                algo.train()
            if action == "visualize":
                algo.visualize()

    except AlgorithmError as e:
        error(e.msg)
        return 1

    except Exception as e:
        error(e)
        return 1
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log-time-stamps", action="store_true", default=False)

    subp = p.add_subparsers(dest="subcmd_name")

    p_train = subp.add_parser("train", formatter_class=argparse.RawTextHelpFormatter)
    p_train.add_argument(
        "--algorithm",
        type=str,
        required=True,
        metavar="algo",
        help="str:   reinforcement learning algorithm algo to use.",
    )
    p_train.add_argument(
        "--environment",
        type=str,
        required=True,
        metavar="env",
        help="str:   minigrid environment env to use.",
    )
    p_train.add_argument(
        "--learning-rate",
        type=float,
        default=None,
        metavar="α",
        help="float: learning rate α to use.",
    )
    p_train.add_argument(
        "--discount-factor",
        type=float,
        default=None,
        metavar="γ",
        help="float: discount factor γ to use.",
    )
    p_train.add_argument(
        "--start-eps",
        type=float,
        default=None,
        metavar="se",
        help="float: anneal epsilon used in greedy-epsilon from se.",
    )
    p_train.add_argument(
        "--end-eps",
        type=float,
        default=None,
        metavar="ee",
        help="float: anneal epsilon used in greedy-epsilon to ee.",
    )
    p_train.add_argument(
        "--annealing-steps",
        type=float,
        default=None,
        metavar="as",
        help="float: decay epsilon over as steps.",
    )
    p_train.add_argument(
        "--updates",
        type=int,
        default=None,
        metavar="n",
        help="int:   train model for up to n updates",
    )
    p_train.add_argument(
        "--render-interval",
        type=int,
        default=None,
        metavar="i",
        help="int:   if i > 0, render every i:th episode",
    )
    p_train.add_argument(
        "--save-interval",
        type=int,
        default=None,
        metavar="j",
        help="int:   if j > 0, save model every j:th episode",
    )
    p_train.add_argument(
        "--model-name",
        type=str,
        default=None,
        metavar="name",
        help="str:   save model as models/<name>.pt when (if) the model is saved",
    )
    p_train.add_argument(
        "--seed", type=int, default=None, metavar="seed", help="int:   seed used for all randomness"
    )
    p_train.add_argument(
        "--fps",
        type=int,
        default=None,
        metavar="fps",
        help="int:   rendering delay = 1/fps + time to compute next action",
    )
    p_train.add_argument("--tensorboard", action="store_true", help="bool:  use tensorboard")
    p_train.set_defaults(action="train")

    p_visualize = subp.add_parser("visualize")
    p_visualize.add_argument(
        "--algorithm",
        type=str,
        required=True,
        metavar="algo",
        help="str:   reinforcement learning algorithm algo to use.",
    )
    p_visualize.add_argument(
        "--environment",
        type=str,
        required=True,
        metavar="env",
        help="str:   minigrid environment env to use.",
    )
    p_visualize.add_argument(
        "--model-name",
        type=str,
        default=None,
        metavar="name",
        help="str:   load model from models/<name>.pt",
    )
    p_visualize.add_argument(
        "--seed", type=int, default=None, metavar="seed", help="int:   seed used for all randomness"
    )
    p_visualize.add_argument(
        "--fps",
        type=int,
        default=None,
        metavar="fps",
        help="int:   rendering delay = 1/fps + time to compute next action",
    )
    p_visualize.set_defaults(action="visualize")

    args = p.parse_args()

    fmt = get_format(args.log_time_stamps)
    config = {"handlers": [{"sink": stderr, "format": fmt}]}
    logger.configure(**config)

    if not hasattr(args, "action"):
        error("You need to select a subcommand {train, visualize}")
        info("\n" + p_train.format_usage() + p_visualize.format_usage())
        return 1
    try:
        result = run(args.action, args)

        debug(f"{args.subcmd_name} returned {result}")
    except KeyboardInterrupt:
        error("Interrupted by user")
        return 1
    return result
