# 必要なモジュールをインポート
from qgis.core import QgsGeometry, QgsFeature, QgsVectorLayer, QgsProject

# 正方形のサイズを指定
# 正方形の一辺の長さ
#0.001で200pxくらい
side_length = 0.001  

layer_name="sq_test"

# 正方形の中心座標を指定 
#地図上で左クリックして座標コピー，ここに貼り付け
center_y, center_x = 37.058877,136.798091
# 正方形の頂点座標を計算
half_side = side_length / 2
vertices = [
    QgsPointXY(center_x - half_side, center_y - half_side),
    QgsPointXY(center_x + half_side, center_y - half_side),
    QgsPointXY(center_x + half_side, center_y + half_side),
    QgsPointXY(center_x - half_side, center_y + half_side),
    QgsPointXY(center_x - half_side, center_y - half_side)  # 最初の頂点に戻る
]


# 正方形のジオメトリを作成
square_geometry = QgsGeometry.fromPolygonXY([vertices])

# 正方形のフィーチャを作成
square_feature = QgsFeature()
square_feature.setGeometry(square_geometry)

# レイヤーを作成または取得
#layer_name = "AllPolygon_nf"
layer = QgsVectorLayer("Polygon?crs=EPSG:4612", layer_name, "memory")
layer.startEditing()
layer.addFeature(square_feature)
layer.commitChanges()

# プロジェクトにレイヤーを追加
QgsProject.instance().addMapLayer(layer)
