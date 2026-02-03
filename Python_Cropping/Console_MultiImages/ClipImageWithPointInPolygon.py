#4番目に実行
#クリップ用ポリゴン内に含まれるポイントを検出し、CSVに出力するスクリプト
import os
import csv
import math
from PIL import Image
from qgis.core import (
    QgsProject, QgsRasterLayer, QgsVectorLayer, QgsGeometry
)
from qgis import processing

# ============ 設定セクション ============
# クリップ用ポリゴンディレクトリ
vector_dir = r"C:\Users\kyohe\Aerial_Photo_Classifier\20260124Data\SquarePolygons\Damaged"

# ターゲット画像ディレクトリ
tif_dir = r"C:\Users\kyohe\Aerial_Photo_Classifier\20260124Data\PatchTIFF_NotRotated\Damaged"
png_dir = r"C:\Users\kyohe\Aerial_Photo_Classifier\20260124Data\PatchPNG\Damaged"

# 出力CSV
output_csv = r"C:\Users\kyohe\Aerial_Photo_Classifier\20260124Data\damaged_polygon_point_mapping.csv"

# ポイントレイヤ名
point_layer_name = "monzen_all"

# ============ 出力ディレクトリの作成 ============
if not os.path.exists(tif_dir):
    os.makedirs(tif_dir)
if not os.path.exists(png_dir):
    os.makedirs(png_dir)

# ============ ポイントレイヤの取得 ============
point_layer = None
layers = QgsProject.instance().mapLayers().values()
for lyr in layers:
    if lyr.name() == point_layer_name and isinstance(lyr, QgsVectorLayer):
        point_layer = lyr
        break

if point_layer is None:
    raise Exception(f"エラー: ポイントレイヤ '{point_layer_name}' が見つかりません")

print(f"ポイントレイヤ '{point_layer_name}' を読み込みました")

# ============ 結果格納用リスト ============
results = []

# ============ フォルダ内のfgbファイルをループ ============
vector_files = [f for f in os.listdir(vector_dir) if f.lower().endswith('.fgb')]
print(f"処理対象ファイル数: {len(vector_files)}")

for idx, fgb_file in enumerate(vector_files, 1):
    print(f"\n[{idx}/{len(vector_files)}] 処理中: {fgb_file}")
    
    fgb_path = os.path.join(vector_dir, fgb_file)
    
    # ============ ベクターレイヤの読み込み ============
    vlayer = QgsVectorLayer(fgb_path, os.path.splitext(fgb_file)[0], 'ogr')
    if not vlayer.isValid():
        print(f"  ⚠️  レイヤ読み込み失敗: {fgb_file} (スキップ)")
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
    
    # ============ ポリゴン内のポイントを検出 ============
    features = list(vlayer.getFeatures())
    if len(features) == 0:
        print(f"  ⚠️  ポリゴンが存在しません: {fgb_file} (スキップ)")
        continue
    
    # 最初のポリゴンを取得（複数ある場合は最初の1つ）
    polygon_geom = features[0].geometry()
    
    if polygon_geom.isEmpty():
        print(f"  ⚠️  ポリゴンジオメトリが空です: {fgb_file} (スキップ)")
        continue
    
    # ============ ポイントレイヤ内のポイントと交差判定 ============
    contained_fids = []
    
    for point_feature in point_layer.getFeatures():
        point_geom = point_feature.geometry()
        
        # ポイントがポリゴン内に含まれているか判定
        if polygon_geom.contains(point_geom):
            fid = point_feature.id()
            contained_fids.append(fid)
    
    # ============ 結果の記録 ============
    if len(contained_fids) > 0:
        print(f"  ✓ {len(contained_fids)}個のポイントを検出しました")
        
        # 1つのポリゴンに対して、ポイント1つ1つを行として出力
        for fid in contained_fids:
            results.append({
                'vector_filename': fgb_file,
                'point_fid': fid
            })
    else:
        print(f"  - ポイントが含まれていません (記録なし)")
    
    # ============ 画像クリッピング処理 ============
    # ラスタレイヤの取得（QGISプロジェクト内のラスタレイヤをスキャン）
    raster_layers = [lyr for lyr in QgsProject.instance().mapLayers().values() 
                     if isinstance(lyr, QgsRasterLayer)]
    
    clipped = False
    for raster_layer in raster_layers:
        # ラスタレイヤ名とfgbファイル名の対応を確認
        raster_name = raster_layer.name()
        # 簡易的な対応：raster_name がfgb_fileの先頭を含むかチェック
        polygon_base_name = os.path.splitext(fgb_file)[0]
        
        if polygon_base_name in raster_name or raster_name.startswith(polygon_base_name[:3]):
            print(f"  画像クリッピング中: {raster_name}")
            
            clip_output = os.path.join(
                tif_dir,
                f'{polygon_base_name}.tif'
            )
            
            try:
                processing.run("gdal:cliprasterbymasklayer", {
                    'INPUT': raster_layer.source(),
                    'MASK': vlayer,
                    'SOURCE_CRS': raster_layer.crs().authid(),
                    'TARGET_CRS': raster_layer.crs().authid(),
                    'CROP_TO_CUTLINE': True,
                    'KEEP_RESOLUTION': True,
                    'OUTPUT': clip_output
                })
                
                print(f"  ✓ TIF保存: {clip_output}")
                clipped = True
            except Exception as e:
                print(f"  ⚠️  クリッピング失敗: {str(e)}")

            try:
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
            except Exception as e:
                print(f"  ⚠️  PNG出力失敗: {str(e)}")
    
    if not clipped:
        print(f"  - 対応するラスタレイヤが見つかりません")

# ============ CSV出力 ============
print(f"\n{'='*50}")
print(f"CSV出力中... ({len(results)}件の記録)")

try:
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['vector_filename', 'point_fid'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✓ CSV保存完了: {output_csv}")
except Exception as e:
    print(f"⚠️  CSV保存失敗: {str(e)}")

print(f"\n処理完了")
print(f"ポイント検出済みポリゴン: {len([r for r in results])} 件")
