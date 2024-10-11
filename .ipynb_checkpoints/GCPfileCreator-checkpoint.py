#画像を読み込んでそのサイズを取得し，対応させる四隅の座標のCSVをもらってGCPファイルを作る
from PIL import Image
import pandas as pd
import glob
from  pathlib import Path
import numpy as np

date='0105'

csvpath=str(Path(r'./'+date+r'/imagesizes.csv'))

# 画像を読み込む
path=str(Path(r'./'+date+r'/LargePNG'))
imglist=list(sorted(Path(path).glob("*")))

namelist=[]
lengthlist=[]
widthlist=[]

for img in imglist:
    image = Image.open(img)
    namelist.append(str(img).split("/")[-1])
    lengthlist.append(image.size[0])
    widthlist.append(image.size[1])

df=pd.DataFrame(data=namelist, lengthlist, widthlist)
df.to_csv(csvpath)
print(csv saved!)