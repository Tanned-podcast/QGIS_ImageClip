from qgis.core import *
from qgis.PyQt.QtCore import QVariant
import math

vectorlayer_name = "road_centerline_clipped"

def create_square_polygons():
    # アクティブなレイヤーを取得
    layer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]
    if not layer or layer.type() != QgsMapLayer.VectorLayer:
        print("ベクターレイヤーを選択してください。")
        return

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
    last_polygon_geom = None  # 直前のポリゴンのジオメトリ

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
            interval = square_size_degrees/2
            
            # ラインの長さを取得
            length = geom.length()
            
            # 間隔ごとにポイントを生成
            current_distance = 0
            last_polygon_geom = None  # ラインごとにリセット
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
                
                # 直前のポリゴンとIoU判定
                if last_polygon_geom is not None:
                    inter = last_polygon_geom.intersection(square_polygon)
                    union = last_polygon_geom.combine(square_polygon)
                    if not union.isEmpty():
                        iou = inter.area() / union.area()
                        if 0.33 <= iou <= 0.34:
                            # 破棄して次へ
                            current_distance += interval
                            continue
                
                # 追加・更新
                feature = QgsFeature()
                feature.setGeometry(square_polygon)
                features.append(feature)
                last_polygon_geom = square_polygon

                current_distance += interval

    # フィーチャをレイヤーに追加
    square_provider.addFeatures(features)
    
    # レイヤーをプロジェクトに追加
    QgsProject.instance().addMapLayer(square_layer)
    
    print("道路幅員に応じた正方形ポリゴンの作成が完了しました。")

# 関数を実行
create_square_polygons()
