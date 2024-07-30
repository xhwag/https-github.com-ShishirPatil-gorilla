from typing import Dict, List

import numpy as np
import os
import glob
from bfcl.types import TestCategory
from bfcl.eval_client import constants
from bfcl.utils.utils import load_json_file
from bfcl.eval_client.constants import *
from bfcl.utils.evaluator_utils import calculate_weighted_accuracy, calculate_unweighted_accuracy
from collections import defaultdict


class Leaderboard:
    def __init__(self) -> None:
        # TODO: Switch to defaultdict
        self.table = {}

    def record_score(self, model_name, test_category, accuracy, total_count):
        if model_name not in self.table:
            self.table[model_name] = {}
            self.table[model_name][test_category] = {
                "accuracy": accuracy,
                "total_count": total_count,
            }

    def record_cost_latency(self, model_name, model_output_data):
        if model_name not in self.table:
            self.table[model_name] = {}
            self.table[model_name]["cost"] = {
                "input_data": [],
                "output_data": [],
            }
            self.table[model_name]["latency"] = []

        input_token = []
        output_token = []
        latency = []
        for data in model_output_data:
            if "latency" in data:
                latency.append(data["latency"])
                if data["latency"] > 60:
                    print("*" * 100)
                    print(
                        f"❗️Warning: Latency for one of {model_name} response is {data['latency']}."
                    )
                    print("*" * 100)
            if "input_token_count" in data:
                if data["input_token_count"] != 0:
                    input_token.append(data["input_token_count"])
            if "output_token_count" in data:
                if data["output_token_count"] != 0:
                    output_token.append(data["output_token_count"])

        self.table[model_name]["cost"]["input_data"].extend(input_token)
        self.table[model_name]["cost"]["output_data"].extend(output_token)
        self.table[model_name]["latency"].extend(latency)

    @staticmethod
    def get_metric(model_name, cost_data, latency_data):

        cost, mean_latency, std_latency, percentile_95_latency = (
            "N/A",
            "N/A",
            "N/A",
            "N/A",
        )

        if (
            model_name in INPUT_PRICE_PER_MILLION_TOKEN
            and len(cost_data["input_data"]) > 0
            and len(cost_data["output_data"]) > 0
        ):

            mean_input_token = np.mean(cost_data["input_data"])
            mean_output_token = np.mean(cost_data["output_data"])
            cost = (
                mean_input_token * INPUT_PRICE_PER_MILLION_TOKEN[model_name]
                + mean_output_token * OUTPUT_PRICE_PER_MILLION_TOKEN[model_name]
            ) / 1000
            cost = round(cost, 2)

        if model_name in OSS_LATENCY:
            mean_latency, std_latency, percentile_95_latency = (
                OSS_LATENCY[model_name] / 1700,
                "N/A",
                "N/A",
            )
            mean_latency = round(mean_latency, 2)
            cost = mean_latency * 1000 * V100_x8_PRICE_PER_HOUR / 3600
            cost = round(cost, 2)

        elif len(latency_data) != 0:
            mean_latency = np.mean(latency_data)
            std_latency = np.stdev(latency_data)
            percentile_95_latency = np.percentile(latency_data, 95)
            mean_latency = round(mean_latency, 2)
            std_latency = round(std_latency, 2)
            percentile_95_latency = round(percentile_95_latency, 2)

            if model_name not in INPUT_PRICE_PER_MILLION_TOKEN:
                cost = sum(latency_data) * V100_x8_PRICE_PER_HOUR / 3600
                cost = round(cost, 2)

        if model_name in NO_COST_MODELS:
            cost = "N/A"

        return cost, mean_latency, std_latency, percentile_95_latency

    def generate_leaderboard_csv(self, output_path):
        data = []
        for model_name, value in self.table.items():
            model_name_escaped = model_name.replace("_", "/")

            python_simple_ast = value.get("simple", {"accuracy": 0, "total_count": 0})
            python_multiple_ast = value.get(
                "multiple_function", {"accuracy": 0, "total_count": 0}
            )
            python_parallel_ast = value.get(
                "parallel_function", {"accuracy": 0, "total_count": 0}
            )
            python_parallel_multiple_ast = value.get(
                "parallel_multiple_function", {"accuracy": 0, "total_count": 0}
            )
            python_simple_exec = value.get(
                "executable_simple", {"accuracy": 0, "total_count": 0}
            )
            python_multiple_exec = value.get(
                "executable_multiple_function", {"accuracy": 0, "total_count": 0}
            )
            python_parallel_exec = value.get(
                "executable_parallel_function", {"accuracy": 0, "total_count": 0}
            )
            python_parallel_multiple_exec = value.get(
                "executable_parallel_multiple_function",
                {"accuracy": 0, "total_count": 0},
            )
            java_simple_ast = value.get("java", {"accuracy": 0, "total_count": 0})
            javascript_simple_ast = value.get(
                "javascript", {"accuracy": 0, "total_count": 0}
            )
            rest_simple_exec = value.get("rest", {"accuracy": 0, "total_count": 0})
            relevance = value.get("relevance", {"accuracy": 0, "total_count": 0})

            cost_data = value.get("cost", {"input_data": [], "output_data": []})
            latency_data = value.get("latency", [])

            simple_ast = calculate_weighted_accuracy(
                [python_simple_ast, java_simple_ast, javascript_simple_ast]
            )
            multiple_ast = python_multiple_ast
            parallel_ast = python_parallel_ast
            parallel_multiple_ast = python_parallel_multiple_ast
            simple_exec = calculate_weighted_accuracy(
                [python_simple_exec, rest_simple_exec]
            )
            multiple_exec = python_multiple_exec
            parallel_exec = python_parallel_exec
            parallel_multiple_exec = python_parallel_multiple_exec

            summary_ast = calculate_unweighted_accuracy(
                [simple_ast, multiple_ast, parallel_ast, parallel_multiple_ast]
            )
            summary_exec = calculate_unweighted_accuracy(
                [simple_exec, multiple_exec, parallel_exec, parallel_multiple_exec]
            )
            overall_accuracy = calculate_weighted_accuracy(
                [
                    simple_ast,
                    multiple_ast,
                    parallel_ast,
                    parallel_multiple_ast,
                    simple_exec,
                    multiple_exec,
                    parallel_exec,
                    parallel_multiple_exec,
                    relevance,
                ]
            )

            cost, latency_mean, latency_std, percentile_95_latency = self.get_metric(
                model_name_escaped, cost_data, latency_data
            )

            if overall_accuracy["total_count"] != 1700:
                print("-" * 100)
                print(
                    f"❗️Warning: Total count for {model_name} is {overall_accuracy['total_count']}"
                )

            data.append(
                [
                    "N/A",
                    overall_accuracy["accuracy"],
                    MODEL_METADATA_MAPPING[model_name_escaped][0],
                    MODEL_METADATA_MAPPING[model_name_escaped][1],
                    MODEL_METADATA_MAPPING[model_name_escaped][2],
                    MODEL_METADATA_MAPPING[model_name_escaped][3],
                    summary_ast["accuracy"],
                    summary_exec["accuracy"],
                    simple_ast["accuracy"],
                    python_simple_ast["accuracy"],
                    java_simple_ast["accuracy"],
                    javascript_simple_ast["accuracy"],
                    multiple_ast["accuracy"],
                    parallel_ast["accuracy"],
                    parallel_multiple_ast["accuracy"],
                    simple_exec["accuracy"],
                    python_simple_exec["accuracy"],
                    rest_simple_exec["accuracy"],
                    multiple_exec["accuracy"],
                    parallel_exec["accuracy"],
                    parallel_multiple_exec["accuracy"],
                    relevance["accuracy"],
                    cost,
                    latency_mean,
                    latency_std,
                    percentile_95_latency,
                ]
            )

        data.sort(key=lambda x: x[1], reverse=True)
        for i in range(len(data)):
            data[i][0] = str(i + 1)
            data[i][1] = "{:.2f}%".format(data[i][1] * 100)
            for j in range(6, len(data[i]) - 4):
                data[i][j] = "{:.2f}%".format(data[i][j] * 100)
            for j in range(len(data[i]) - 4, len(data[i])):
                data[i][j] = str(data[i][j])

        data.insert(0, COLUMNS)

        filepath = os.path.join(output_path, "data.csv")
        with open(filepath, "w") as f:
            for i, row in enumerate(data):
                if i < len(data) - 1:
                    f.write(",".join(row) + "\n")
                else:
                    f.write(",".join(row))

    def update_leaderboard_table_with_score_file(self, score_path):

        entries = os.scandir(score_path)

        # Filter out the subdirectories
        subdirs = [entry.path for entry in entries if entry.is_dir()]

        # Traverse each subdirectory
        for subdir in subdirs:
            # Pattern to match JSON files in this subdirectory
            json_files_pattern = os.path.join(subdir, "*.json")
            model_name = subdir.split(score_path)[1]
            # Find and process all JSON files in the subdirectory
            for model_score_json in glob.glob(json_files_pattern):
                metadata = load_json_file(model_score_json)[0]
                accuracy, total_count = metadata["accuracy"], metadata["total_count"]
                test_category = model_score_json.split("_score.json")[0].split("/")[-1]
                if model_name not in self.table:
                    self.table[model_name] = {}
                if test_category not in self.table[model_name]:
                    self.table[model_name][test_category] = {
                        "accuracy": accuracy,
                        "total_count": total_count,
                    }
