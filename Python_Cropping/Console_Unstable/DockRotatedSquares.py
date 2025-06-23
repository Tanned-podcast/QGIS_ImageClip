from qgis.core import *
from qgis.PyQt.QtCore import QVariant
import math

vectorlayer_name = "road_centerline_clipped"

# 正方形のサイズと間隔（度単位）
square_size = 0.0003
interval = 0.0003


def get_angle(geom):
    # 頂点リスト取得
    pts = geom.asPolygon()[0]
    # 一辺の長さ（頂点0→1間の距離）
    edge_length = math.hypot(pts[1].x() - pts[0].x(), pts[1].y() - pts[0].y())
    distance = edge_length / 2
    # QgsPointXYで線分を作成
    line = QgsGeometry.fromPolylineXY([QgsPointXY(pts[0]), QgsPointXY(pts[1])])
    return line.interpolateAngle(distance)

def align_polygons_by_angle(layer):
    # 1. フィーチャ取得（2つと仮定）
    features = list(layer.getFeatures())
    if len(features) < 2:
        raise ValueError("2つ以上のポリゴンが必要です")
    featA, featB = features[0], features[1]
    geomA = featA.geometry()
    geomB = featB.geometry()

    # 2. 各ポリゴンの頂点0→1の角度を取得
    angleA = get_angle(geomA)
    angleB = get_angle(geomB)
    #print(f"angleA: {angleA*180/math.pi:.2f}°, angleB: {angleB*180/math.pi:.2f}°")

    # 3. 角度差分
    diff_angle = (angleB - angleA) % (2*math.pi)
    diff_angle_deg = diff_angle * 180 / math.pi
    #print(f"角度差分: {diff_angle_deg:.2f}°")

    # 4. 角度差分に応じた頂点ペアの辞書（例：必要に応じて変更可）
    #角度差分を45度で割った余りの階級と，ポリゴンAの頂点番号，ポリゴンBの頂点番号
    vertex_pair_dict = {
        0: (2, 3),
        1: (0, 0),
        2: (1, 3),
        3: (3, 0),
        4: (0, 3),
        5: (2, 0),
        6: (3, 3),
        7: (1, 0),
    }
    # どの階級かを決定
    bin_idx = int(diff_angle_deg // 45) % 8
    idxA, idxB = vertex_pair_dict[bin_idx]
    #print(f"対応する辞書ID:{bin_idx}, 対応する頂点ペア: idxA={idxA}, idxB={idxB}")

    ptsA = geomA.asPolygon()[0]
    ptsB = geomB.asPolygon()[0]

    # 5. 平行移動ベクトル計算
    vec_x = ptsA[idxA].x() - ptsB[idxB].x()
    vec_y = ptsA[idxA].y() - ptsB[idxB].y()

    # 6. ポリゴンBに平行移動を適用
    geomB.translate(vec_x, vec_y)
    #print(f"頂点同士を対応、ベクトル({vec_x:.3f},{vec_y:.3f}) 移動しました。")

    # レイヤの編集モードでジオメトリを更新
    layer.startEditing()
    layer.changeGeometry(featB.id(), geomB)
    layer.commitChanges()

    return geomB


def create_square_polygons():
    # アクティブなレイヤーを取得
    layer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]
    if not layer or layer.type() != QgsMapLayer.VectorLayer:
        print("ベクターレイヤーを選択してください。")
        return

    # 新しいポリゴンレイヤーを作成
    square_layer = QgsVectorLayer("Polygon?crs=EPSG:4612", "正方形ポリゴン", "memory")
    square_provider = square_layer.dataProvider()

    # フィーチャを格納するリスト
    features = []
    # 直前のポリゴンジオメトリを保持
    prev_geom = None

    # 各ラインに対して処理
    for feature in layer.getFeatures():
        geom = feature.geometry()
        if geom.type() == QgsWkbTypes.LineGeometry:
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
                half_size = square_size / 2
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
                # 2つ目以降の場合、直前のポリゴンと頂点を合わせる
                if prev_geom is not None:
                    # 一時レイヤ作成
                    temp_layer = QgsVectorLayer("Polygon?crs=EPSG:4612", "temp", "memory")
                    temp_provider = temp_layer.dataProvider()
                    # 直前と現在のポリゴンを一時レイヤに追加
                    temp_featA = QgsFeature()
                    temp_featA.setGeometry(prev_geom)
                    temp_featB = QgsFeature()
                    temp_featB.setGeometry(square_polygon)
                    temp_provider.addFeatures([temp_featA, temp_featB])
                    # 頂点合わせ
                    aligned_geom = align_polygons_by_angle(temp_layer)
                    # --- ここから中心点補正 ---
                    center = aligned_geom.centroid().asPoint()
                    vec_cx = point_xy.x() - center.x()
                    vec_cy = point_xy.y() - center.y()
                    aligned_geom.translate(vec_cx, vec_cy)
                    # --- ここまで中心点補正 ---
                    square_polygon = aligned_geom
                # フィーチャ作成
                feature = QgsFeature()
                feature.setGeometry(square_polygon)
                features.append(feature)
                # prev_geomを更新
                prev_geom = square_polygon
                # 次の位置へ移動
                current_distance += interval

    # フィーチャをレイヤーに追加
    square_provider.addFeatures(features)
    
    # レイヤーをプロジェクトに追加
    QgsProject.instance().addMapLayer(square_layer)
    
    print("正方形ポリゴンの作成が完了しました。")

# 関数を実行
create_square_polygons()
