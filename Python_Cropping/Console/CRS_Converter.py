# QGIS Python Console用 - ポリゴンレイヤーのCRS変換
# EPSG:6668 (JGD2011 \ Japan Plane Rectangular CS) から EPSG:4612 (JGD2000 \ Japan Geodetic Datum 2000) に変換

from qgis.core import QgsProject, QgsVectorLayer
import processing
from pathlib import Path

# ユーザーが変更可能な設定
LAYER_NAME = "17204_tokei"  # ここに変換したいレイヤー名を入力してください
SOURCE_CRS_EPSG = 6668  # 元のCRSのEPSGコード
TARGET_CRS_EPSG = 4612  # 変換先のCRSのEPSGコード
OUTPUT_FILE_PATH = str(Path(r"C:\Users\kyohe\石川県基盤地図情報\都市計画区域ポリゴン\A55-22_17204_GML\EPSG4612_"+LAYER_NAME))


def convert_layer_crs(layer_name, source_crs_epsg=6668, target_crs_epsg=4612):
    """
    指定されたレイヤーのCRSを変換する関数（Processingツール使用）
    
    Parameters:
    layer_name (str): 変換対象のレイヤー名
    source_crs_epsg (int): 元のCRSのEPSGコード（デフォルト: 6668）
    target_crs_epsg (int): 変換先のCRSのEPSGコード（デフォルト: 4612）
    """
    
    # プロジェクトからレイヤーを取得
    layer = QgsProject.instance().mapLayersByName(layer_name)
    
    if not layer:
        print(f"エラー: レイヤー '{layer_name}' が見つかりません")
        return False
    
    layer = layer[0]  # 最初のマッチしたレイヤーを取得
    
    # 現在のCRSを確認
    current_crs = layer.crs()
    print(f"現在のCRS: {current_crs.description()} (EPSG:{current_crs.authid().split(':')[1]})")
    
    # 変換先のCRSを設定
    target_crs = f"EPSG:{target_crs_epsg}"
    
    # Processingツールを使用してCRS変換
    params = {
        'INPUT': layer,
        'TARGET_CRS': target_crs,
        'OUTPUT': 'memory:'
    }
    
    try:
        result = processing.run("native:reprojectlayer", params)
        new_layer = result['OUTPUT']
        
        # 新しいレイヤーに名前を設定
        new_layer.setName(f"{layer_name}_EPSG{target_crs_epsg}")
        
        # プロジェクトに新しいレイヤーを追加
        QgsProject.instance().addMapLayer(new_layer)
        
        print(f"CRS変換完了: {layer_name} -> {layer_name}_EPSG{target_crs_epsg}")
        print(f"変換されたフィーチャー数: {new_layer.featureCount()}")
        
        return True
        
    except Exception as e:
        print(f"エラー: CRS変換に失敗しました - {str(e)}")
        return False

def save_converted_layer_to_file(layer_name, output_path, source_crs_epsg=6668, target_crs_epsg=4612):
    """
    レイヤーのCRSを変換してファイルに保存する関数
    
    Parameters:
    layer_name (str): 変換対象のレイヤー名
    output_path (str): 出力ファイルのパス（例: "C:\temp\converted_layer.gpkg"）
    source_crs_epsg (int): 元のCRSのEPSGコード（デフォルト: 6668）
    target_crs_epsg (int): 変換先のCRSのEPSGコード（デフォルト: 4612）
    """
    
    # プロジェクトからレイヤーを取得
    layer = QgsProject.instance().mapLayersByName(layer_name)
    
    if not layer:
        print(f"エラー: レイヤー '{layer_name}' が見つかりません")
        return False
    
    layer = layer[0]
    
    # 変換先のCRSを設定
    target_crs = f"EPSG:{target_crs_epsg}"
    
    # Processingツールを使用してCRS変換（ファイル出力）
    params = {
        'INPUT': layer,
        'TARGET_CRS': target_crs,
        'OUTPUT': output_path
    }
    
    try:
        result = processing.run("native:reprojectlayer", params)
        print(f"CRS変換完了: {layer_name} -> {output_path}")
        print(f"変換されたフィーチャー数: {result['OUTPUT']}")
        
        return True
        
    except Exception as e:
        print(f"エラー: CRS変換に失敗しました - {str(e)}")
        return False


print("=== QGIS CRS変換ツール ===")
print(f"変換対象レイヤー: {LAYER_NAME}")
print(f"元のCRS: EPSG:{SOURCE_CRS_EPSG}")
print(f"変換先CRS: EPSG:{TARGET_CRS_EPSG}")
print()


# レイヤー名がデフォルト値の場合は警告
if LAYER_NAME == "変換したいレイヤー名":
    print("⚠️  警告: LAYER_NAMEを実際のレイヤー名に変更してください")
    print("例: LAYER_NAME = 'my_polygon_layer'")
    print()

# CRS変換を実行
if LAYER_NAME != "変換したいレイヤー名":
    print("CRS変換を実行中...")
    
    # メモリレイヤーとして変換
    success = save_converted_layer_to_file(LAYER_NAME, OUTPUT_FILE_PATH, SOURCE_CRS_EPSG, TARGET_CRS_EPSG)
    
    if success:
        print("\n✅ CRS変換が正常に完了しました")
    else:
        print("\n❌ CRS変換に失敗しました")
else:
    print("レイヤー名を設定してから再実行してください")

print("\nCRS変換処理が完了しました。")
