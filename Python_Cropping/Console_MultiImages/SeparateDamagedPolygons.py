# 2番目に実行、被害ありなしの分離
# QGISのPythonコンソールで実行
from qgis.core import QgsProject, QgsVectorLayer

from pathlib import Path
from datetime import datetime
import os

# 処理開始時間の記録
resultspath = r"C:\Users\kyohe\ishikawa_QGIS_ImageClipPolygon\TimeCalc_Result\SeparateDamagedPolygons"
region = "suzu"
os.makedirs(resultspath, exist_ok=True)  # 結果保存フォルダがなければ作成
starttime = datetime.now().strftime('%Y%m%d_%H%M%S')
startdate = datetime.now().strftime('%Y%m%d')


point_layer_name = "suzu_all"
polygon_layer_name = "Square_LYurban"

# 点地物レイヤー
point_layer = QgsProject.instance().mapLayersByName(point_layer_name)[0]

# プロジェクト内の全ポリゴンレイヤー（IntersectionDeletedを含むもののみ）を取得
layers = QgsProject.instance().mapLayers().values()
polygon_layers = [lyr for lyr in layers if lyr.type() == QgsVectorLayer.VectorLayer and polygon_layer_name in lyr.name()]

for polygon_layer in polygon_layers:
    # 出力用レイヤ名をレイヤごとにユニークに
    intact_layer_name = f"{polygon_layer.name()}_intact"
    house_collapse_layer_name = f"{polygon_layer.name()}_house_collapse"
    other_damage_layer_name = f"{polygon_layer.name()}_other_damage"

    # 出力用メモリレイヤー作成
    crs = polygon_layer.crs().toWkt()
    polygon_fields = polygon_layer.fields()

    layerC = QgsVectorLayer(f'Polygon?crs={crs}', intact_layer_name, 'memory')
    layerC.dataProvider().addAttributes(polygon_fields)
    layerC.updateFields()

    layerD = QgsVectorLayer(f'Polygon?crs={crs}', house_collapse_layer_name, 'memory')
    layerD.dataProvider().addAttributes(polygon_fields)
    layerD.updateFields()

    layerE = QgsVectorLayer(f'Polygon?crs={crs}', other_damage_layer_name, 'memory')
    layerE.dataProvider().addAttributes(polygon_fields)
    layerE.updateFields()

    # ポリゴンごとに内部の点を調べる
    for poly_feat in polygon_layer.getFeatures():
        poly_geom = poly_feat.geometry()
        inside_points = []
        for pt_feat in point_layer.getFeatures():
            if poly_geom.contains(pt_feat.geometry()):
                inside_points.append(pt_feat)
        # 点が1つも含まれない場合 → C
        if not inside_points:
            layerC.dataProvider().addFeature(poly_feat)
        else:
            # 含まれる点のうち house_collapse=True/False を判定
            has_true = any(pt['house_collapse'] for pt in inside_points)
            has_false = any(not pt['house_collapse'] for pt in inside_points)
            if has_true:
                layerD.dataProvider().addFeature(poly_feat)
            if has_false:
                layerE.dataProvider().addFeature(poly_feat)

    # レイヤーをプロジェクトに追加
    QgsProject.instance().addMapLayer(layerC)
    QgsProject.instance().addMapLayer(layerD)
    #QgsProject.instance().addMapLayer(layerE)

    print(f"{polygon_layer.name()} の処理が完了しました。C, D, Eレイヤーが追加されました。")

print("全てのIntersectionDeletedポリゴンレイヤの処理が完了しました。")

# 計算終了時間の取得とフォーマット
finishtime = datetime.now().strftime('%Y%m%d_%H%M%S')
datepath=str(Path(resultspath + f"\calc_time_SeparateDamagedPolygons_{region}_{startdate}.txt"))

# ファイルを新規作成し、日付を書き込む
with open(datepath, 'w', encoding='utf-8') as f:
    f.write(starttime)
    f.write(finishtime)

print("Calculation Finished in ", finishtime)
