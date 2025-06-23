#先にノードレイヤを空撮の範囲に合わせてクリップしとけ
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry
)
from qgis.PyQt.QtCore import QVariant

#レイヤ名前
polygon_layer_name="sq_test"
node_layer_name="output"

#IoUがどれくらい被ってたら削除するか
IoU_threshold=0.7

# レイヤ取得
polygon_layer = QgsProject.instance().mapLayersByName(polygon_layer_name)[0]
node_layer = QgsProject.instance().mapLayersByName(node_layer_name)[0]

if not polygon_layer.isValid() or not node_layer.isValid():
    print("レイヤーの読み込みに失敗しました")
    exit()

# 結果を格納するリスト
features_to_delete = set()

# 各ノードごとに処理
for node_feat in node_layer.getFeatures():
    node_geom = node_feat.geometry()
    # ノードを含むポリゴンを抽出
    containing_polygons = []
    for poly_feat in polygon_layer.getFeatures():
        if poly_feat.id() in features_to_delete:
            continue  # 既に削除予定ならスキップ
        if poly_feat.geometry().contains(node_geom):
            containing_polygons.append(poly_feat)

    # IoU計算と重複削除
    for i in range(len(containing_polygons)):
        for j in range(i + 1, len(containing_polygons)):
            geom1 = containing_polygons[i].geometry()
            geom2 = containing_polygons[j].geometry()
            inter = geom1.intersection(geom2)
            union = geom1.combine(geom2)
            if union.isEmpty():
                continue
            iou = inter.area() / union.area()
            if iou >= IoU_threshold:
                # 片方を削除リストに追加（ここではj側を削除）
                features_to_delete.add(containing_polygons[j].id())

# 実際に削除
#with edit(polygon_layer):
#    for fid in features_to_delete:
#        polygon_layer.deleteFeature(fid)

# 新規メモリレイヤを作成
crs = polygon_layer.crs().toWkt()
fields = polygon_layer.fields()
result_layer = QgsVectorLayer(f'Polygon?crs={crs}', '重複除去ポリゴン', 'memory')
result_layer.startEditing()
result_layer.dataProvider().addAttributes(fields)
result_layer.updateFields()

# 削除対象でないポリゴンのみ追加
for feat in polygon_layer.getFeatures():
    if feat.id() not in features_to_delete:
        result_layer.addFeature(feat)
result_layer.commitChanges()

# プロジェクトに追加
QgsProject.instance().addMapLayer(result_layer)

print(f"{len(features_to_delete)}個の重複ポリゴンを除去した新レイヤを作成しました")
