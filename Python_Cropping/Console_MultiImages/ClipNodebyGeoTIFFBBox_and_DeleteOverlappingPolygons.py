#交差点ノードを広域空撮の範囲で切り取り（計算軽くする），切り取った各ノードを使って交差点上のポリゴン削除
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsVectorFileWriter
import processing
import os
import re

#ポリゴンの出力先 広域空撮の撮影日時に合わせて変えること！！
output_dir = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\SquarePatchPolygons"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

vectorlayer_name="全道路ノード"

# 全域交差点ノードレイヤ取得
vector_layer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]

# プロジェクト内のラスタレイヤ取得
layers = QgsProject.instance().mapLayers().values()
raster_layers = [lyr for lyr in layers if lyr.type() == QgsMapLayer.RasterLayer]

#プロジェクト内の正方形ポリゴンレイヤ取得（レイヤ名に"Square"を含むもののみ）
polygon_layers = [lyr for lyr in layers if lyr.type() == QgsMapLayer.VectorLayer and "Square" in lyr.name()]

clipped_vector_layers = []

#IoUがどれくらい被ってたら削除するか
IoU_threshold=0.7

def extract_number(name):
    # 例: "a1", "a2" などの番号部分を抽出
    m = re.search(r'[a-zA-Z]\d+', name)
    return m.group(0) if m else None

def delete_polygon_at_intersection(node_layer, polygon_layer, output_dir="./", output_format="FlatGeobuf"):
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

    # ファイル名を生成
    output_path = os.path.join(
        output_dir,
        f"{polygon_layer.name()}_IntersectionDeleted.fgb"
    )

    # ファイルとして保存
    QgsVectorFileWriter.writeAsVectorFormat(
        result_layer,
        output_path,
        "UTF-8",
        result_layer.crs(),
        output_format
    )

    print(f"{len(features_to_delete)}個の重複ポリゴンを除去した新レイヤを {output_path} に保存しました")



##メイン処理　各ラスタ画像に対して
for raster in raster_layers:
    # ラスタのBoundingBoxで交差点ノードレイヤをクリッピング
    extent = raster.extent()
    xmin = extent.xMinimum()
    xmax = extent.xMaximum()
    ymin = extent.yMinimum()
    ymax = extent.yMaximum()
    crs = raster.crs().authid()
    ext_str = f"{xmin},{xmax},{ymin},{ymax} [{crs}]"

    params = {
        'INPUT': vector_layer,
        'EXTENT': ext_str,
        'CLIP': True,
        'OUTPUT': 'memory:'
    }
    res = processing.run("qgis:extractbyextent", params)
    clipped_layer = res['OUTPUT']
    clipped_layer.setName(f"{vector_layer.name()}_clipped_{raster.name()[:]}")

    # 結果を現在の QGIS プロジェクトへ追加
    QgsProject.instance().addMapLayer(clipped_layer)
    clipped_vector_layers.append(clipped_layer)



for node_layer in clipped_vector_layers:
    node_num = extract_number(node_layer.name())
    if not node_num:
        print(f"ノードレイヤ名から番号が抽出できません: {node_layer.name()}")
        continue

    # 番号が一致するポリゴンレイヤを探す
    matched_polygon = None
    for poly_layer in polygon_layers:
        poly_num = extract_number(poly_layer.name())
        if poly_num == node_num:
            matched_polygon = poly_layer
            break

    if matched_polygon is None:
        print(f"対応するポリゴンレイヤが見つかりません: {node_layer.name()}")
        continue
    
    print(node_layer.name())
    print(poly_layer.name())
    
    delete_polygon_at_intersection(node_layer, matched_polygon, output_dir=output_dir)

print("全ラスタ画像範囲での交差点ノードクリッピング＆正方形ポリゴン作成が完了しました。")