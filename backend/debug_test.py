import traceback
import asyncio
import io
import main

async def test():
    try:
        from fastapi import UploadFile
        cv = UploadFile(filename='cv.txt', file=io.BytesIO(b'hola soy consultor con power bi y python y 3 anos d exp.'))
        
        from pptx import Presentation
        prs = Presentation()
        prs.save('test_val.pptx')
        
        with open('test_val.pptx', 'rb') as f:
            ppt = UploadFile(filename='p.pptx', file=io.BytesIO(f.read()))

        res = await main.procesar_documentos(cv=cv, plantilla=ppt, contexto=' ')
        print('Exito:', res)
    except Exception as e:
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
