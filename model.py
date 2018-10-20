import pandas
import re
import numpy as np
world_data = pandas.read_csv("epa-sea-level_csv.csv", header=0)
world_data.drop(world_data.columns[2:5], axis=1, inplace=True)
world_data.drop(134, axis=0, inplace=True)
temperature_df = pandas.read_csv("annual_csv.csv", header=0)
temperature = list()
for num in temperature_df.index:
    if num > 268:
        break
    if num % 2 != 0:
        temperature.append((temperature_df.loc[num - 1, "Mean"] + temperature_df.loc[num, "Mean"]) / 2.0)
ice_data = pandas.read_csv("glaciers_csv.csv", header=0)
ice_data["Change"] = np.nan
for num in ice_data.index:
    if num == 69:
        ice_data.drop(num, axis=0, inplace=True)
    else:
        ice_data.loc[num, "Change"] = ice_data.loc[num + 1, "Mean cumulative mass balance"] - ice_data.loc[num, "Mean cumulative mass balance"]
for num in list(range(66)):
    world_data.drop(num, axis=0, inplace=True)
world_data.reset_index(inplace=True)
world_data["Mean Ice Mass Loss"] = ice_data["Change"]
world_data["Temp"] = temperature[::-1][66:]


import sklearn
from sklearn.ensemble import (RandomForestRegressor, AdaBoostRegressor, ExtraTreesRegressor, GradientBoostingRegressor)
from sklearn.svm import SVC
import xgboost

#WE ARE STILL MISSING TEST DATA, WE WILL MOST LIKELY NEED TO INTERPOLATE

training_data = world_data
ntrain = training_data.shape[0]
Y = training_data["CSIRO Adjusted Sea Level"]
training_data.drop(["CSIRO Adjusted Sea Level", "Year"], axis=1, inplace=True)
ntest = test_data.shape[0]
SEED = 0
FOLDS = 5
kfold = sklearn.model_selection.KFold(n_splits=FOLDS, random_state=SEED)
random_forest = RandomForestRegressor(n_estimators=575, warm_start=True, max_depth=5, min_samples_leaf=2, max_features="sqrt", random_state=SEED, verbose=False)
extra_trees = ExtraTreesRegressor(n_estimators=575, max_depth=5, min_samples_leaf=3, random_state=SEED, verbose=False)
ada_boost = AdaBoostRegressor(n_estimators=575, learning_rate=0.95, random_state=SEED)
gradient_boosting = GradientBoostingRegressor(n_estimators=575,  max_depth=5, min_samples_leaf=3, random_state=SEED, verbose=False)
svc = SVC(kernel="linear", C=0.025, random_state=SEED)
base_predictions_train = pandas.DataFrame()
classifier_names = {random_forest: "Random_Forest", extra_trees: "Extra_Trees", ada_boost: "Ada_Boost", gradient_boosting: "Gradient_Boosting", svc: "SVC"}
train_list = list()
test_list = list()
for classifier in [random_forest, extra_trees, ada_boost, gradient_boosting, svc]:
    oof_train = numpy.zeros((ntrain,))
    oof_test = numpy.zeros((ntest,))
    oof_test_kf = numpy.zeros((FOLDS, ntest))
    num = 0
    for train_index, test_index in kfold.split(training_data):
        x_tr = X_train[train_index]
        y_tr = Y_train[train_index]
        x_te = X_train[test_index]
        classifier.fit(x_tr, y_tr)
        oof_train[test_index] = classifier.predict(x_te)
        oof_test_kf[num, :] = classifier.predict(X_test)
        num += 1
    oof_test[:] = oof_test_kf.mean(axis=0)
    base_predictions_train[classifier_names[classifier]] = oof_train.reshape(-1, 1).ravel()
    train_list.append(oof_train.reshape(-1, 1))
    test_list.append(oof_test.reshape(-1, 1))
x_train = numpy.concatenate([train for train in train_list], axis=1)
x_test = numpy.concatenate([test for test in test_list], axis=1)
booster = xgboost.XGBClassifier(n_estimators=5000, learning_rate=0.95, max_depth=4, min_child_weight=2,  gamma=1, subsample=0.8, colsample_by_tree=1, objective="binary:logistic", scale_pos_weight=1, silent=True)
booster.fit(x_train, Y_train)
predictions = booster.predict(x_test)
