import grid_operations.grid_operations as gridops
import pandas as pd
from constants import BEARING_ANGLE_DEG
from utils import generate_combinations
from test import get_model_predictions_on_test_dataset
import glob
import sys


# parameters which don't require retraining
remove_outliers = False
use_probability_weighting = False
probability_weighting_k = 3
# parameters which don't require retraining

dataset_type = "normal"
model_type = "lstm"
CHECKPOINT_FOLDER = "grid_search_checkpoints"


# combined_test_measurement_filename = "erlangen_test_dataset_minadjusted.csv"
if dataset_type == "time-idx" :
    combined_test_measurement_filename = "Erlangen-test-timeidx-minadjusted.csv"
elif dataset_type == "normal":
    combined_test_measurement_filename = "erlangen_test_dataset_minadjusted.csv"
elif dataset_type == "gpx":
    combined_test_measurement_filename = "Erlangen-15-02-2023-test-minadjusted-gpx.csv"
else:
    sys.exit("Wrong dataset type.")

GRID_WIDTH = 800
GRID_HEIGHT = 800
grid_element_length = 20
normalize = True
augmentation_count = 0
augmentation_distance_m = 20
# network parameters


num_prev_steps_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
input_features_list = [7, 10, 13, 16, 19] if dataset_type == "time-idx" else [6, 9, 12, 15, 18]
parameter_lists = [num_prev_steps_list, input_features_list]
parameter_combinations = generate_combinations(parameter_lists)
mean_distance_result = []

for param_comb in parameter_combinations:
    print("\n\n")
    print(param_comb)

    num_prev_steps = param_comb[0]
    input_features = param_comb[1]

    label_df, augmented_df, grid_lines, label_file_path, augmented_file_path = gridops.load(
        combined_test_measurement_filename,
        "../datasets", grid_element_length)

    cols = len(grid_lines["vertical_lines"]) - 1
    rows = len(grid_lines["horizontal_lines"]) - 1
    output_classes = cols * rows

    checkpoint_folder = f"{CHECKPOINT_FOLDER}/{model_type}_{input_features}_grid{grid_element_length}_prev{num_prev_steps}{'_normalized' if normalize else ''}_minadjusted{'_augmented' + str(augmentation_count) + '-' + str(augmentation_distance_m) if augmentation_count > 0 else ''}"

    files = sorted(glob.glob(checkpoint_folder + '/*'))
    last_epoch = int((files[-1].split("_")[-1]).split(".")[0])

    if dataset_type == "normal":
        train_x_directory = f"../datasets/erlangen_dataset_minadjusted_gridlen{grid_element_length}.csv"
        train_y_directory = f"../datasets/erlangen_dataset_minadjusted_gridlen{grid_element_length}_label.csv"
        test_x_directory = f"../datasets/erlangen_test_dataset_minadjusted_gridlen{grid_element_length}.csv"
        test_y_directory = f"../datasets/erlangen_test_dataset_minadjusted_gridlen{grid_element_length}_label.csv"
    elif dataset_type == "gpx":
        train_x_directory = f"../datasets/Erlangen-15-02-2023-train-minadjusted-gpx_gridlen{grid_element_length}.csv"
        train_y_directory = f"../datasets/Erlangen-15-02-2023-train-minadjusted-gpx_gridlen{grid_element_length}_label.csv"
        test_x_directory = f"../datasets/Erlangen-15-02-2023-test-minadjusted-gpx_gridlen{grid_element_length}.csv"
        test_y_directory = f"../datasets/Erlangen-15-02-2023-test-minadjusted-gpx_gridlen{grid_element_length}_label.csv"
    elif dataset_type == "time-idx":
        train_x_directory = f"../datasets/Erlangen-train-timeidx-minadjusted_gridlen{grid_element_length}.csv"
        train_y_directory = f"../datasets/Erlangen-train-timeidx-minadjusted_gridlen{grid_element_length}_label.csv"
        test_x_directory = f"../datasets/Erlangen-test-timeidx-minadjusted_gridlen{grid_element_length}.csv"
        test_y_directory = f"../datasets/Erlangen-test-timeidx-minadjusted_gridlen{grid_element_length}_label.csv"
    else:
        print("Wrong dataset type.")
        break

    prediction_grid_indices, label_grid_indices, prediction_probability_distributions = get_model_predictions_on_test_dataset(
        restored_checkpoint=last_epoch,
        checkpoint_folder=checkpoint_folder,
        output_classes=output_classes,
        input_features=input_features,
        test_x_directory=test_x_directory,
        test_y_directory=test_y_directory,
        batch_size=16,
        num_prev_steps=num_prev_steps,
        train_x_directory=train_x_directory,
        train_y_directory=train_y_directory,
        normalize=normalize,
        model_type=model_type
    )

    if use_probability_weighting is False:
        prediction_coordinates_df = gridops.grid_index_to_coordinates(grid_lines, prediction_grid_indices)
    else:
        prediction_coordinates_df = gridops.probability_distribution_to_coordinates(grid_lines,
                                                                                    prediction_probability_distributions,
                                                                                    grid_element_length,
                                                                                    BEARING_ANGLE_DEG,
                                                                                    k=probability_weighting_k)

    label_coordinates_df = label_df[["latitude", "longitude"]]

    offset_corrected_label_coordinates_df = gridops.correct_offset(label_coordinates_df, prediction_coordinates_df)

    if remove_outliers:
        prediction_coordinates_df, offset_corrected_label_coordinates_df = gridops.remove_outliers(
            prediction_coordinates_df, offset_corrected_label_coordinates_df, 30, 3)

    distance_df = gridops.get_prediction_label_distance_df(prediction_coordinates_df,
                                                           offset_corrected_label_coordinates_df)

    # print(distance_df)
    pred_label_df = pd.concat([prediction_coordinates_df, offset_corrected_label_coordinates_df], axis=1)
    pred_label_df.columns = ["prediction_longitude", "prediction_latitude", "label_longitude", "label_latitude"]
    pred_label_df = pred_label_df.join(distance_df)

    print("Mean distance (m): ", pred_label_df["distance"].mean())
    mean_distance_result.append(pred_label_df["distance"].mean())

print("Mean Distances: ")
for idx, dist in enumerate(mean_distance_result):
    if (idx+1) % len(num_prev_steps_list) == 0:
        print(f"{dist:.1f}", end="\n")
    else:
        print(f"{dist:.1f}", end="\t")
