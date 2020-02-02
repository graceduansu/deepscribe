import luigi
from .training import TrainKerasModelFromDefinitionTask
from .ml_input import AssignDatasetTask
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np
import os
import tensorflow.keras as kr
import tensorflow as tf
import matplotlib
from pathlib import Path

matplotlib.use("Agg")
# import matplotlib.backends.backend_pdf
import matplotlib.pyplot as plt


# produces confusion matrics from test data
class TestModelTask(luigi.Task):
    imgfolder = luigi.Parameter()
    hdffolder = luigi.Parameter()
    modelsfolder = luigi.Parameter()
    target_size = luigi.IntParameter()  # standardizing to square images
    keep_categories = luigi.ListParameter()
    fractions = luigi.ListParameter()  # train/valid/test fraction
    model_definition = luigi.Parameter()  # JSON file with model definition specs
    num_augment = luigi.IntParameter(default=0)
    rest_as_other = luigi.BoolParameter(
        default=False
    )  # set the remaining as "other" - not recommended for small keep_category lengths

    def requires(self):
        return {
            "model": TrainKerasModelFromDefinitionTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            "dataset": AssignDatasetTask(
                self.imgfolder,
                self.hdffolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.num_augment,
                self.rest_as_other,
            ),
        }

    def run(self):
        # load TF model and dataset
        model = kr.models.load_model(self.input()["model"].path)
        data = np.load(self.input()["dataset"].path)

        # make predictions on data

        # (batch_size, num_classes)
        pred_logits = model.predict(data["test_imgs"])

        # computing predicted labels
        pred_labels = np.argmax(pred_logits, axis=1)

        # compute confusion matrix

        confusion = confusion_matrix(data["test_labels"], pred_labels)

        np.save(self.output().path, confusion)

    def output(self):
        p = Path(self.model_definition)
        p_data = Path(self.input().path)

        return luigi.LocalTarget(
            "{}/{}_{}/test_confusion.npy".format(self.modelsfolder, p.stem, p_data.stem)
        )


class PlotConfusionMatrixTask(luigi.Task):
    imgfolder = luigi.Parameter()
    hdffolder = luigi.Parameter()
    modelsfolder = luigi.Parameter()
    target_size = luigi.IntParameter()  # standardizing to square images
    keep_categories = luigi.ListParameter()
    fractions = luigi.ListParameter()  # train/valid/test fraction
    model_definition = luigi.Parameter()  # JSON file with model definition specs
    num_augment = luigi.IntParameter(default=0)
    rest_as_other = luigi.BoolParameter(
        default=False
    )  # set the remaining as "other" - not recommended for small keep_category lengths

    def requires(self):
        return {
            "confusion_matrix": TestModelTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            "dataset": AssignDatasetTask(
                self.imgfolder,
                self.hdffolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.num_augment,
                self.rest_as_other,
            ),
        }

    def run(self):
        # load matrix

        confusion = np.load(self.input()["confusion_matrix"].path)

        # get labels from dataset

        data = np.load(self.input()["dataset"].path)

        class_labels = data["classes"]
        fig = plt.figure(figsize=(13, 13))
        ax = fig.add_subplot(111)
        plt.title("Confusion matrix")
        cax = ax.matshow(confusion)
        fig.colorbar(cax)

        # appending extra tick label to make sure everything aligns properly
        ax.set_xticklabels(list(class_labels[:1]) + list(class_labels))
        ax.set_yticklabels(list(class_labels[:1]) + list(class_labels))
        plt.savefig(self.output().path)

    def output(self):
        p = Path(self.model_definition)
        p_data = Path(self.input().path)

        return luigi.LocalTarget(
            "{}/{}_{}/confustion_test.png".format(
                self.modelsfolder, p.stem, p_data.stem
            )
        )


class GenerateClassificationReportTask(luigi.Task):
    imgfolder = luigi.Parameter()
    hdffolder = luigi.Parameter()
    modelsfolder = luigi.Parameter()
    target_size = luigi.IntParameter()  # standardizing to square images
    keep_categories = luigi.ListParameter()
    fractions = luigi.ListParameter()  # train/valid/test fraction
    model_definition = luigi.Parameter()  # JSON file with model definition specs
    num_augment = luigi.IntParameter(default=0)
    rest_as_other = luigi.BoolParameter(
        default=False
    )  # set the remaining as "other" - not recommended for small keep_category lengths

    def requires(self):
        return {
            "model": TrainKerasModelFromDefinitionTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            "dataset": AssignDatasetTask(
                self.imgfolder,
                self.hdffolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.num_augment,
                self.rest_as_other,
            ),
        }

    def run(self):
        # load TF model and dataset
        model = kr.models.load_model(self.input()["model"].path)
        data = np.load(self.input()["dataset"].path)

        # make predictions on data

        # (batch_size, num_classes)
        pred_logits = model.predict(data["test_imgs"])

        # computing predicted labels
        pred_labels = np.argmax(pred_logits, axis=1)

        # compute confusion matrix

        report = classification_report(
            data["test_labels"], pred_labels, target_names=data["classes"]
        )

        with self.output().temporary_path() as temppath:
            with open(temppath, "w") as outf:
                outf.write(report)

    def output(self):
        p = Path(self.model_definition)
        p_data = Path(self.input().path)

        return luigi.LocalTarget(
            "{}/{}_{}/classification_report.txt".format(
                self.modelsfolder, p.stem, p_data.stem
            )
        )


class PlotMisclassificationTopKTask(luigi.Task):
    imgfolder = luigi.Parameter()
    hdffolder = luigi.Parameter()
    modelsfolder = luigi.Parameter()
    target_size = luigi.IntParameter()  # standardizing to square images
    keep_categories = luigi.ListParameter()
    fractions = luigi.ListParameter()  # train/valid/test fraction
    model_definition = luigi.Parameter()  # JSON file with model definition specs
    num_augment = luigi.IntParameter(default=0)
    rest_as_other = luigi.BoolParameter(
        default=False
    )  # set the remaining as "other" - not recommended for small keep_category lengths
    k = luigi.IntParameter(default=5)

    def requires(self):
        return {
            "model": TrainKerasModelFromDefinitionTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            "dataset": AssignDatasetTask(
                self.imgfolder,
                self.hdffolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.num_augment,
                self.rest_as_other,
            ),
        }

    def run(self):

        os.mkdir(self.output().path)

        # load TF model and dataset
        model = kr.models.load_model(self.input()["model"].path)
        data = np.load(self.input()["dataset"].path)

        # make predictions on data

        # (batch_size, num_classes)
        pred_logits = model.predict(data["test_imgs"])

        # (batch_size,)
        in_top_k = kr.backend.in_top_k(pred_logits, data["test_labels"], self.k)

        in_top_k_arr = tf.Session().run([in_top_k])

        # get indices of datapoints that aren't in the top k

        num_incorrect = int(np.sum(np.logical_not(in_top_k_arr)))

        print(data["test_imgs"].shape)
        print(np.logical_not(in_top_k_arr).shape)
        # (num_incorrect, img_size_x, img_size_y, img_depth)
        incorrect_top_5 = data["test_imgs"][
            np.squeeze(np.logical_not(in_top_k_arr)), :, :
        ]
        # (num_incorrect,)
        incorrect_top_5_truth = data["test_labels"][
            np.squeeze(np.logical_not(in_top_k_arr))
        ]
        # (num_incorrect, num_classes)
        incorrect_logits = pred_logits[np.squeeze(np.logical_not(in_top_k_arr)), :]

        for i in range(num_incorrect):
            img = np.squeeze(incorrect_top_5[i, :, :])
            ground_truth = data["classes"][incorrect_top_5_truth[i]]
            top_k_predictions = np.argsort(incorrect_logits[i, :])[0 : self.k]
            top_k_predicted_labels = data["classes"][top_k_predictions]

            fig = plt.figure()
            plt.title(
                f"Misclassified Image {i} - predicted {top_k_predicted_labels}, truth {ground_truth}"
            )
            plt.imshow(img, cmap="gray")

            plt.savefig(f"{self.output().path}/misclassified-{i}.png")
            plt.close(fig)

    def output(self):
        p = Path(self.model_definition)
        p_data = Path(self.input().path)

        return luigi.LocalTarget(
            "{}/{}_{}/test_misclassified".format(self.modelsfolder, p.stem, p_data.stem)
        )


# plots a random sample of 16 incorrect images from test..
class PlotIncorrectTask(luigi.Task):
    imgfolder = luigi.Parameter()
    hdffolder = luigi.Parameter()
    modelsfolder = luigi.Parameter()
    target_size = luigi.IntParameter()  # standardizing to square images
    keep_categories = luigi.ListParameter()
    fractions = luigi.ListParameter()  # train/valid/test fraction
    model_definition = luigi.Parameter()  # JSON file with model definition specs
    num_augment = luigi.IntParameter(default=0)
    rest_as_other = luigi.BoolParameter(
        default=False
    )  # set the remaining as "other" - not recommended for small keep_category lengths

    def requires(self):
        return {
            "model": TrainKerasModelFromDefinitionTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            "dataset": AssignDatasetTask(
                self.imgfolder,
                self.hdffolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.num_augment,
                self.rest_as_other,
            ),
        }

    def run(self):

        # load TF model and dataset
        model = kr.models.load_model(self.input()["model"].path)
        data = np.load(self.input()["dataset"].path)

        # make predictions on data

        # (batch_size, num_classes)
        pred_logits = model.predict(data["test_imgs"])

        # (batch_size,)

        pred_labels = np.argmax(pred_logits, axis=1)

        incorrect_prediction_idx, = np.not_equal(
            data["test_labels"], pred_labels
        ).nonzero()

        f, axarr = plt.subplots(5, 5, figsize=(10, 10))

        for i, (ix, iy) in enumerate(np.ndindex(axarr.shape)):

            indx = incorrect_prediction_idx[i]
            img = np.squeeze(data["test_imgs"][indx, :, :])
            ground_truth = data["classes"][data["test_labels"][indx]]
            pred_label = data["classes"][pred_labels[indx]]

            ax = axarr[ix, iy]
            ax.set_title(f"{pred_label},  {ground_truth}")
            ax.imshow(img, cmap="gray")

        plt.savefig(self.output().path)

    def output(self):
        p = Path(self.model_definition)
        p_data = Path(self.input().path)

        return luigi.LocalTarget(
            "{}/{}_{}/test_misclassified_sample.png".format(
                self.modelsfolder, p.stem, p_data.stem
            )
        )


# runs the collection of analysis tasks on the
class RunAnalysisOnTestDataTask(luigi.WrapperTask):
    imgfolder = luigi.Parameter()
    hdffolder = luigi.Parameter()
    modelsfolder = luigi.Parameter()
    target_size = luigi.IntParameter()  # standardizing to square images
    keep_categories = luigi.ListParameter()
    fractions = luigi.ListParameter()  # train/valid/test fraction
    model_definition = luigi.Parameter()  # JSON file with model definition specs
    num_augment = luigi.IntParameter(default=0)
    rest_as_other = luigi.BoolParameter(
        default=False
    )  # set the remaining as "other" - not recommended for small keep_category lengths
    k = luigi.IntParameter(default=5)

    def requires(self):
        return [
            GenerateClassificationReportTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            PlotConfusionMatrixTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
            PlotIncorrectTask(
                self.imgfolder,
                self.hdffolder,
                self.modelsfolder,
                self.target_size,
                self.keep_categories,
                self.fractions,
                self.model_definition,
                self.num_augment,
                self.rest_as_other,
            ),
        ]