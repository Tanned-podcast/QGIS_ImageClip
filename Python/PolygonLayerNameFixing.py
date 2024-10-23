from qgis.core import QgsProject
#レイヤの名前がnn_1-n_1とかになるのをまとめてnn_1のみに直すコード
#レイヤ名が必ず偶数文字数になるので2で割ればいい


# QGISのAPIからプロジェクトインスタンスを取得
project = QgsProject.instance()

# すべてのレイヤを取得
all_layers = project.mapLayers().values()

# レイヤごとに名前を変更
for layer in all_layers:
    new_name = layer.name()[:int((len(layer.name()))/2)]
    layer.setName(new_name)
