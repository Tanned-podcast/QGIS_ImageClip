# 現在プロジェクトに使用されているレイヤの名前一覧を出力
from qgis.core import QgsProject

layer_names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]

# 保存先ファイルパス（例としてデスクトップに出力）
output_path =r"C:/Users/kyohe/ishikawa_QGIS_ImageClipPolygon/layernames.txt"  # 適宜書き換えてください

with open(output_path, 'w', encoding='utf-8') as f:
    for name in layer_names:
        f.write(name)
        f.write("\n")

print(f"レイヤ名を {output_path} に保存しました。")
