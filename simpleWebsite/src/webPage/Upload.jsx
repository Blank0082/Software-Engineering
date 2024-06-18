import Navbar from "../components/Navbar";
import {useContext, useEffect, useState} from "react";
import {useNavigate} from "react-router-dom";
import axios from "axios";
import '../css/upload.css'
import {AuthContext} from "../components/AuthContext";

function Upload() {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [previewUrls, setPreviewUrls] = useState([]);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [currentPreviewIndex, setCurrentPreviewIndex] = useState(0);
    const [filesName, setFilesName] = useState([]);
    const navigate = useNavigate();
    const {isLoggedIn, authChecked} = useContext(AuthContext);

    useEffect(() => {
        if (authChecked && !isLoggedIn) {
            navigate("/login");
        }
    }, [isLoggedIn, authChecked, navigate]);

    const onFileChange = event => {
        const files = Array.from(event.target.files);
        const validFiles = files.filter(file => file.type === "image/png" || file.type === "image/jpeg");

        if (validFiles.length !== files.length) {
            setUploadStatus("Only PNG and JPG files are allowed.");
            return;
        }

        setFilesName(validFiles.map(file => file.name));
        setSelectedFiles(validFiles);
        setPreviewUrls(validFiles.map(file => URL.createObjectURL(file)));
        setCurrentPreviewIndex(0);
    };
    const onFileUpload = () => {
        if (selectedFiles.length === 0) {
            setUploadStatus("Please select a file first.");
            return;
        }
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append("files", file, file.name);
        });
        axios.post("http://localhost:5000/upload", formData, {withCredentials: true})
            .then(response => {
                console.log(response.data.results);
                setUploadStatus("File(s) uploaded successfully!");
                navigate("/result", { state: { results: response.data.results } });
            })
            .catch(error => {
                if (error.response && error.response.status === 401) {
                    //創建未驗證使用者畫面
                    navigate("/");
                } else {
                    console.log(error.response.data)
                    setUploadStatus("File upload failed on server.");
                }
            });
    }
    const handlePrevImage = () => {
        setCurrentPreviewIndex((prevIndex) => (prevIndex === 0 ? previewUrls.length - 1 : prevIndex - 1));
    };

    const handleNextImage = () => {
        setCurrentPreviewIndex((prevIndex) => (prevIndex === previewUrls.length - 1 ? 0 : prevIndex + 1));
    };

    return (
        <div className="upload-page list-container">
            <Navbar/>
            <div className="upload-container">
                <h2>Upload a File</h2>
                <input
                    type="file"
                    id="file-input"
                    onChange={onFileChange}
                    accept="image/jpeg,image/png"
                    multiple
                    style={{display: 'none'}}
                />
                <button onClick={() => document.getElementById('file-input').click()} className="btn_style">
                    選擇檔案
                </button>
                {previewUrls.length > 0 && (
                    <>
                        <span>File name:{filesName[currentPreviewIndex]}</span>
                        <div className="image-preview-container">
                            {currentPreviewIndex !== 0 &&
                                <button onClick={handlePrevImage} className="btn_style">上一張</button>
                            }
                            <img src={previewUrls[currentPreviewIndex]} alt="Preview" />
                            {currentPreviewIndex !== selectedFiles.length - 1 &&
                                <button onClick={handleNextImage} className="btn_style">下一張</button>
                            }
                        </div>
                        <span>File: {currentPreviewIndex + 1}/{selectedFiles.length}</span>
                        <span>{uploadStatus}</span>
                        <button onClick={onFileUpload} className="btn_style">開始辨識</button>
                    </>
                )}
            </div>
        </div>
    )
}

export default Upload;