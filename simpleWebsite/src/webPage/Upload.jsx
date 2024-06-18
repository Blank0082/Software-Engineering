import Navbar from "../components/Navbar";
import { useContext, useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import '../css/upload.css'
import { AuthContext } from "../components/AuthContext";

function Upload() {
    const [selectedFiles, setSelectedFiles] = useState([]);
    const [previewUrls, setPreviewUrls] = useState([]);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [currentPreviewIndex, setCurrentPreviewIndex] = useState(0);
    const [filesName, setFilesName] = useState([]);
    const navigate = useNavigate();
    const { isLoggedIn, authChecked } = useContext(AuthContext);

    const handlePrevImage = useCallback(() => {
        setCurrentPreviewIndex((prevIndex) => (prevIndex === 0 ? previewUrls.length - 1 : prevIndex - 1));
    }, [previewUrls.length]);

    const handleNextImage = useCallback(() => {
        setCurrentPreviewIndex((prevIndex) => (prevIndex === previewUrls.length - 1 ? 0 : prevIndex + 1));
    }, [previewUrls.length]);

    useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === 'ArrowLeft') {
                handlePrevImage();
            } else if (event.key === 'ArrowRight') {
                handleNextImage();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    }, [handlePrevImage, handleNextImage]);

    useEffect(() => {
        if (authChecked && !isLoggedIn) {
            //創建重新登入畫面
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
        //創建loading畫面
        axios.post("http://localhost:5000/upload", formData, { withCredentials: true })
            .then(response => {
                console.log(response.data.results);
                setUploadStatus("File(s) uploaded successfully!");
                navigate("/result", { state: { results: response.data.results } });
            })
            .catch(error => {
                if (error.response && error.response.status === 400)
                    setUploadStatus("File upload failed. Please try again.");
                else if (error.response && error.response.status === 401) {
                    //創建未驗證使用者畫面
                    navigate("/");
                }
                else if (error.response && error.response.status === 413) {
                    setUploadStatus("File size exceeds the limit.limit is 30MB.");
                }
                else if (error.response && error.response.status === 500) {
                    setUploadStatus("Server error. Please try again later.");
                    console.log(error.response.data);
                } else {
                    setUploadStatus('Network error. Please try again later.');
                }
            });
    }

    return (
        <div className="upload-page list-container">
            <Navbar />
            <div className="upload-container">
                <h2>Upload a File</h2>
                <input
                    type="file"
                    id="file-input"
                    onChange={onFileChange}
                    accept="image/jpeg,image/png"
                    multiple
                    style={{ display: 'none' }}
                />
                <button onClick={() => document.getElementById('file-input').click()} className="upload-btn">
                    選擇檔案
                </button>
                {previewUrls.length > 0 && (
                    <>
                        <span>File name:{filesName[currentPreviewIndex]}</span>
                        <div className="upload-image-container">
                            <button onClick={handlePrevImage} className="first-of-type">&lt;</button>
                            <img src={previewUrls[currentPreviewIndex]} alt="Preview" />
                            <button onClick={handleNextImage} className="last-of-type">&gt;</button>
                        </div>
                        <span>張數: {currentPreviewIndex + 1}/{selectedFiles.length}</span>
                        <span className="upload-status">{uploadStatus}</span>
                        <button onClick={onFileUpload} className="upload-btn">開始辨識</button>
                    </>
                )}
            </div>
        </div>
    )
}

export default Upload;