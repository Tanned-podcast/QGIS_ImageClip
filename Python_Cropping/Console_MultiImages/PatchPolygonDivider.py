#道路線に沿って配置されたポリゴンが入ったベクタレイヤで，各ポリゴンを個別のFGBファイルに出力
import os
from qgis.core import *
import re
from pathlib import Path

output_dir_intact =  r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\SqPatchPolygons\Intact"
output_dir_house = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\SqPatchPolygons\HouseCollapse"
output_dir_otherdamage =  r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\SqPatchPolygons\OtherDamage"

# 出力ディレクトリがなければ作成
if not os.path.exists(output_dir_intact):
    os.makedirs(output_dir_intact)
if not os.path.exists(output_dir_house):
    os.makedirs(output_dir_house)
if not os.path.exists(output_dir_otherdamage):
    os.makedirs(output_dir_otherdamage)

# プロジェクト内のベクタレイヤを取得　被害ありなしで分けた後の正方形ポリゴンのみ
layers = QgsProject.instance().mapLayers().values()
intact_layers = [lyr for lyr in layers if isinstance(lyr, QgsVectorLayer) and "intact" in lyr.name()]
house_layers = [lyr for lyr in layers if isinstance(lyr, QgsVectorLayer) and "house_collapse" in lyr.name()]
otherdamage_layers = [lyr for lyr in layers if isinstance(lyr, QgsVectorLayer) and "other_damage" in lyr.name()]

def Divide_SqPolygons(layer, output_dir, damage_class:str):
    # レイヤ名から英字＋数字のパターン（例: a1, b2, c10など）を抽出
    match = re.search(r'[a-zA-Z]+[0-9]+', layer.name())
    if match:
        layer_id = match.group()
    else:
        layer_id = layer.name()  # 該当しない場合はレイヤ名全体を使う

    # 各フィーチャ（ポリゴン）ごとに個別ファイルとして保存
    for i, feature in enumerate(layer.getFeatures()):
        # 新しいメモリレイヤを作成
        crs = layer.crs().toWkt()
        mem_layer = QgsVectorLayer('Polygon?crs=' + crs, f'polygon_{i}', 'memory')
        mem_layer_data = mem_layer.dataProvider()
        # 属性テーブルの構造をコピー
        mem_layer_data.addAttributes(layer.fields())
        mem_layer.updateFields()
        # フィーチャを追加
        mem_layer_data.addFeature(feature)
        mem_layer.updateExtents()
        # 出力ファイル名
        out_path = str(Path(output_dir) + "/" + f"{layer_id}_" + damage_class + f"_{i}.fgb")
        # 保存
        QgsVectorFileWriter.writeAsVectorFormat(mem_layer, out_path, 'UTF-8', mem_layer.crs(), 'FlatGeobuf')
        print(f'保存: {out_path}')

    print(f'{layer.name()}について，全てのポリゴンを個別ファイルとして保存しました。')

def Layers_Loop(layers, output_dir, damage_class):
    for ly in layers:
        Divide_SqPolygons(ly, output_dir, damage_class)

Layers_Loop(intact_layers, output_dir_intact, "Intact")
Layers_Loop(house_layers, output_dir_house, "HouseCollapse")
Layers_Loop(otherdamage_layers, output_dir_otherdamage, "OtherDamage")
