import torch
import shutil
import os
import sys
import json
from recognition import predict, MyEnsemble, paper_cut, transform
import uuid


def create_directories(*paths):
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

def handle_transform(input_path, transform_path):
    code = transform.Transformer(input_path).run(transform_path)
    if code is 1:
        return {"status": "error", "data": "影像無法轉換"}
    elif code is 2:
        return {"status": "error", "data": "影像拉伸錯誤"}
    return None

def handle_split(paper_cutter, transform_path, output_path):
    for filename in os.listdir(transform_path):
        if filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            input_path_img = os.path.join(transform_path, filename)
            code = paper_cutter.split(input_path_img, output_path)
            if code is 3:
                return {"status": "error", "data": "輸入路徑錯誤"}
            elif code is 4:
                return {"status": "error", "data": "切割錯誤"}
            elif code is 5:
                return {"status": "error", "data": "寫入檔案錯誤"}
            elif code is 6:
                return {"status": "error", "data": "切割結果錯誤"}
    return None

def main(input_path):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model_path = "./model/ensamble_stacking.pth"
    model = torch.load(model_path, map_location=device).to(device)

    paper_cutter = paper_cut.GridSplitPaper(HLine=19, VLine=41, girdWidth1=71, girdWidth2=22, girdHeight=71)
    unique_id = str(uuid.uuid4())
    transform_path = f'./tmp/transform_{unique_id}'
    output_path = f'./tmp/output_{unique_id}'
    class_path = './api/classes.txt'
    truth_path = './api/test_truth.txt'

    create_directories('tmp', transform_path, output_path)

    try:
        error = handle_transform(input_path, transform_path)
        if error:
            print(json.dumps(error))
            sys.exit(0)

        error = handle_split(paper_cutter, transform_path, output_path)
        if error:
            print(json.dumps(error))
            sys.exit(0)

        evaluations, predictions = predict(model, output_path, class_path, truth_path)
        first_classes = [pred['predicts'][1]['class'] for pred in predictions]
        result_string = ''.join(first_classes)

        result = {
            "status": "success",
            "data": result_string
        }
    except Exception as e:
        result = {
            "status": "error",
            "data": str(e)
        }
    finally:
        shutil.rmtree(transform_path, ignore_errors=True)
        shutil.rmtree(output_path, ignore_errors=True)

    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"status": "error", "data": "Usage: python app.py <input_file>"}))
        sys.exit(1)
    
    input_path = sys.argv[1]
    main(input_path)