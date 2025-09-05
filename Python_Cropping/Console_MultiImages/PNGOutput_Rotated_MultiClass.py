#一つ一つバラバラの正方形ポリゴンに対して，画像を切り抜いてディレクトリに出力
import os
import re
import math
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsGeometry
)
from qgis import processing
from PIL import Image

#Intact HouseCollapse OtherDamageクラスそれぞれに対して実行
vector_dir = r"C:\Users\kyohe\Aerial-Photo-Classifier\20250826Data\SquarePolygons\Intact\suzu_all"
tif_dir = r"C:\Users\kyohe\Aerial-Photo-Classifier\20250826Data\PatchTIFF_NotRotated\Intact\suzu_all"
png_dir = r"C:\Users\kyohe\Aerial-Photo-Classifier\20250826Data\PatchPNG\Intact\suzu_all"

# プロジェクト内の全ラスタレイヤを取得
layers = QgsProject.instance().mapLayers().values()
raster_layers = [lyr for lyr in layers if isinstance(lyr, QgsRasterLayer)]

# フォルダ内のfgbファイルを取得
vector_files = [f for f in os.listdir(vector_dir) if f.lower().endswith('.fgb')]

for raster_layer in raster_layers:
    print(f"処理中ラスタ: {raster_layer.name()}")
    # ラスタレイヤ名から英字＋数字のパターン（例: a1, b2, c10など）を抽出
    match = re.search(r'[a-zA-Z]+[0-9]+', raster_layer.name())
    if match:
        layer_id = match.group()
    else:
        layer_id = raster_layer.name()  # 該当しない場合はレイヤ名全体を使う

    # ラスタ名を含むベクタファイルだけ抽出（例: a13_a.fgb, a13_b.fgb, a13_c.fgb）
    matching_vector_files = [f for f in vector_files if layer_id in f]
    if len(matching_vector_files) == 0:
        print(f"{layer_id} に対応するベクタファイルが見つかりません")
        continue
    for fgb_file in matching_vector_files:
        fgb_path = os.path.join(vector_dir, fgb_file)
        # ベクターレイヤ読み込み
        vlayer = QgsVectorLayer(fgb_path, os.path.splitext(fgb_file)[0], 'ogr')
        if not vlayer.isValid():
            print(f"レイヤ読み込み失敗: {fgb_file}")
            continue
        # 1ポリゴンのみ前提
        features = list(vlayer.getFeatures())
        if len(features) == 0:
            print(f"ポリゴンが存在しません: {fgb_file}")
            continue
        feature = features[0]
        geom = feature.geometry()
        pts = geom.asPolygon()[0]
        # 頂点0→1の線分の中点で角度を取得
        edge_length = math.hypot(pts[3].x() - pts[0].x(), pts[3].y() - pts[0].y())
        distance = edge_length / 2
        line = QgsGeometry.fromPolylineXY([pts[0], pts[3]])
        angle_rad = line.interpolateAngle(distance)  # ラジアン
        angle_deg = math.degrees(angle_rad)  # degreeに変換

        # クリップ
        clip_output = os.path.join(
            tif_dir,
            f'{os.path.splitext(fgb_file)[0]}.tif'
        )
        processing.run("gdal:cliprasterbymasklayer", {
            'INPUT': raster_layer.source(),
            'MASK': vlayer,
            'SOURCE_CRS': raster_layer.crs().authid(),
            'TARGET_CRS': raster_layer.crs().authid(),
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'OUTPUT': clip_output
        })

        # クリップした画像をPillowで開く
        with Image.open(clip_output) as im:
            if im.mode != 'RGBA':
                im = im.convert('RGBA')
            # 逆回転（expand=Trueで余白も含めて回転）
            rotated = im.rotate(angle_deg, expand=True)
            # アルファチャンネルから不透明部分のbboxを取得
            bbox = rotated.getbbox()
            savepath = os.path.join(
                png_dir,
                f'{os.path.splitext(fgb_file)[0]}.png'
            )
            if bbox:
                cropped = rotated.crop(bbox)
                cropped.save(savepath)
            else:
                rotated.save(savepath)
            #print(f"Clipped Image Saved in {savepath}")

print("All Images Successfully Saved")