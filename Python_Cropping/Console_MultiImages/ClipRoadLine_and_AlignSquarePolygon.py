#DRMの道路データを空撮GeoTIFFの範囲で切り取り（計算を軽くする），切り取った各DRMの線に対して正方形ポリゴン配置
from qgis.core import *
import processing
import math

vectorlayer_name = "DRM_edited"  # 全域道路線レイヤ名

def create_square_polygons(layer):
    
    # 道路幅員属性のインデックスを取得
    width_field_index = layer.fields().indexOf('R22_005')
    if width_field_index == -1:
        print("道路幅員属性が見つかりません。")
        return

    
    # 新しいポリゴンレイヤーを作成
    square_layer = QgsVectorLayer("Polygon?crs=EPSG:4612", "正方形ポリゴン", "memory")
    square_provider = square_layer.dataProvider()

    # 道路幅員に応じた正方形のサイズを定義（メートル単位）
    width_size_mapping_meters = {
        1: 37,  # 幅員階級1
        2: 33.25,   # 幅員階級2
        3: 28.25,   # 幅員階級3
        4: 27    # 幅員階級4
    }

    # フィーチャを格納するリスト
    features = []

    # 各ラインに対して処理
    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom.type() == QgsWkbTypes.LineGeometry:
            # 道路幅員を取得
            road_width = feature.attribute('R22_005')
            if road_width is None or road_width not in width_size_mapping_meters:
                print(f"無効な道路幅員値: {road_width}")
                continue
            
            # 道路幅員に応じた正方形サイズをメートルで取得
            square_size_meters = width_size_mapping_meters[road_width]
            
            # メートルを角度に変換（概算）
            # 日本の緯度での概算：1度 ≈ 111,000メートル
            square_size_degrees = square_size_meters / 111000.0
            interval = square_size_degrees/2  # 間隔も正方形サイズと同じにする
            
            # ラインの長さを取得
            length = geom.length()
            
            # 間隔ごとにポイントを生成
            current_distance = 0
            while current_distance < length:
                #interpolate()によって，1本の道路中心線に沿ってcurrent_distance分だけ進んだ場所の点を取得
                point = geom.interpolate(current_distance)
                point_xy = point.asPoint()  # QgsPointをQgsPointXYに変換
                
                # 現在の点での線分の角度を計算
                # 少し前後の点を取得してそれらから線分の角度を計算
                offset = 0.0001  # 小さなオフセット
                point_before = geom.interpolate(max(0, current_distance - offset)).asPoint()
                point_after = geom.interpolate(min(length, current_distance + offset)).asPoint()
                
                # 線分の角度を計算（ラジアン）
                angle = math.atan2(point_after.y() - point_before.y(), 
                                 point_after.x() - point_before.x())
                
                # 正方形の頂点を計算（回転前）
                half_size = square_size_degrees / 2
                square_points = [
                    QgsPointXY(-half_size, -half_size),
                    QgsPointXY(half_size, -half_size),
                    QgsPointXY(half_size, half_size),
                    QgsPointXY(-half_size, half_size),
                    QgsPointXY(-half_size, -half_size)
                ]
                
                # 頂点を回転させて中心点を移動
                rotated_points = []
                for p in square_points:
                    # 回転行列を使用して点を回転
                    rotated_x = p.x() * math.cos(angle) - p.y() * math.sin(angle)
                    rotated_y = p.x() * math.sin(angle) + p.y() * math.cos(angle)
                    # 中心点を移動
                    rotated_points.append(QgsPointXY(rotated_x + point_xy.x(), 
                                                   rotated_y + point_xy.y()))
                
                # ポリゴンを作成
                square_polygon = QgsGeometry.fromPolygonXY([[point for point in rotated_points]])
                feature = QgsFeature()
                feature.setGeometry(square_polygon)
                features.append(feature)
                
                # 次の位置へ移動
                current_distance += interval

    # フィーチャをレイヤーに追加
    square_provider.addFeatures(features)
    
    # レイヤーをプロジェクトに追加
    QgsProject.instance().addMapLayer(square_layer)
    square_layer.setName(f"Square_{layer.name()[11:]}")

    
    print(f"{square_layer}について，道路幅員に応じた正方形ポリゴンの作成が完了しました。")


# --- メイン処理 ---

# 全域道路線レイヤ取得
vector_layer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]

# プロジェクト内のラスタレイヤ取得
layers = QgsProject.instance().mapLayers().values()
raster_layers = [lyr for lyr in layers if lyr.type() == QgsMapLayer.RasterLayer]

clipped_vector_layers = []

for raster in raster_layers:
    # ラスタのBoundingBoxで道路線レイヤをクリッピング
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
    clipped_layer.setName(f"{vector_layer.name()}_{raster.name()}")

    # 結果を現在の QGIS プロジェクトへ追加
    QgsProject.instance().addMapLayer(clipped_layer)
    clipped_vector_layers.append(clipped_layer)

for clly in clipped_vector_layers:   
    # クリッピングしたレイヤに対して正方形ポリゴン生成
    create_square_polygons(clly)

print("全ラスタ画像範囲での道路線クリッピング＆正方形ポリゴン作成が完了しました。")
