import os
import math
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsGeometry
)
from qgis import processing
from PIL import Image

# 設定
vector_dir = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\misc\SqAlign_MultiWidth_a13_Test"
raster_layer_name = 'a13'
output_dir = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\misc\SqAlign_MultiWidth_a13_Test_PNG"

# ラスタレイヤ取得
raster_layer = QgsProject.instance().mapLayersByName(raster_layer_name)[0]

# フォルダ内のfgbファイルを取得
vector_files = [f for f in os.listdir(vector_dir) if f.lower().endswith('.fgb')]

for fgb_file in vector_files:
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
    #print(f"ポリゴンの回転角：{angle_deg}")

    # クリップ
    clip_output = os.path.join(output_dir, f'clip_{os.path.splitext(fgb_file)[0]}.tif')
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
        savepath=os.path.join(output_dir, f'{os.path.splitext(fgb_file)[0]}.png')
        if bbox:
            cropped = rotated.crop(bbox)
            cropped.save(savepath)
        else:
            rotated.save(savepath)
        
        #print(f"Clipped Image Saved in{savepath}")
        

print("All Images Successfully Saved")