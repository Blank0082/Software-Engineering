import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import axios from 'axios';
import '../css/result.css';

const Result = () => {
    const location = useLocation();
    const { results } = location.state || { results: [] };
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isEditing, setIsEditing] = useState(false);
    const [editedResults, setEditedResults] = useState([]);
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [successResult, setSuccessResult] = useState(0);
    const [errorResult, setErrorResult] = useState(0);

    useEffect(() => {
        if (results.length === 0) {
            navigate('/no-results'); // 導向沒有結果的頁面
        } else {
            const fetchResults = async () => {
                setLoading(true);
                try {
                    const fetchedResults = await Promise.all(
                        results.map(async (result) => {
                            if (result.status === 'success') {
                                const response = await axios.get(`http://localhost:5000/results/${result.filename}`, { withCredentials: true });
                                setSuccessResult(prevSuccessResult => prevSuccessResult + 1);
                                return { ...result, data: response.data.data, originalFilename: response.data.originalFilename };
                            }
                            else {
                                setErrorResult(prevErrorResult => prevErrorResult + 1);
                                return result;
                            }
                        })
                    );
                    setEditedResults(fetchedResults);
                    setLoading(false);
                } catch (error) {
                    console.error('Error fetching results:', error);
                    setLoading(false);
                }
            };

            fetchResults();
        }
    }, [results, navigate]);

    const handlePrevImage = useCallback(() => {
        setCurrentIndex((prevIndex) => (prevIndex === 0 ? results.length - 1 : prevIndex - 1));
        setIsEditing(false);
    }, [results.length]);

    const handleNextImage = useCallback(() => {
        setCurrentIndex((prevIndex) => (prevIndex === results.length - 1 ? 0 : prevIndex + 1));
        setIsEditing(false);
    }, [results.length]);

    useEffect(() => {
        const handleKeyDown = (event) => {
            if (isEditing) return;
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
    }, [isEditing, handlePrevImage, handleNextImage]);

    const handleEditClick = () => {
        setIsEditing(true);
    };

    const handleDownloadClick = () => {
        const result = editedResults[currentIndex];
        if (result.status === 'success') {
            const blob = new Blob([result.data], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = (result.originalFilename).split('.').slice(0, -1).join('.') + '.txt';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    };

    const handleSaveClick = () => {
        const updatedResults = [...editedResults];
        updatedResults[currentIndex].data = editedResults[currentIndex].data;
        setEditedResults(updatedResults);
        setIsEditing(false);
    };

    const handleCancelClick = () => {
        setIsEditing(false);
    };

    const handleSaveAllClick = () => {
        if (window.confirm('確定保存所有更改嗎？')) {
            axios.post("http://localhost:5000/saveResults", { results: editedResults }, { withCredentials: true })
                .then(response => {
                    alert('保存成功');
                    navigate('/history');
                })
                .catch(error => {
                    if (error.response && error.response.status === 401) {
                        alert('請先登入');
                        navigate('/login');
                    } else if (error.response && error.response.status === 403) {
                        console.error('Forbidden:', error.response.data);
                        alert('Forbidden');
                    } else if (error.response && error.response.status === 500) {
                        console.error('Server Error:', error.response.data);
                        alert('Sever Error');
                    } else {
                        console.error('Server Error:', error);
                        alert('Sever Error');
                    }
                });
        }
    };

    const renderContent = () => {
        if (loading) {
            return <div className="loading-spinner">loading...</div>;
        }

        if (!editedResults[currentIndex]) {
            return <div>沒有結果顯示</div>;
        }

        if (isEditing) {
            return (
                <>
                    <textarea
                        value={editedResults[currentIndex].data}
                        onChange={(event) => {
                            const updatedResults = [...editedResults];
                            updatedResults[currentIndex].data = event.target.value;
                            setEditedResults(updatedResults);
                        }}
                    />
                    <div>
                        <button className="save" onClick={handleSaveClick}>保存</button>
                        <button className="cancel" onClick={handleCancelClick}>取消</button>
                    </div>
                </>
            );
        }

        if (editedResults[currentIndex].status === 'error') {
            return <div className="show-text-container-error">原因：{editedResults[currentIndex].data}</div>;
        }

        return (
            <>
                <div className="show-text-container">{editedResults[currentIndex].data}</div>
                <div className="result-buttons">
                    <button className="edit" onClick={handleEditClick}>修改</button>
                    <button className="download" onClick={handleDownloadClick}>下載</button>
                </div>
            </>
        );
    };

    return (
        <div className="result-page">
            <Navbar />
            <div className="result-container list-container">
                <h2 className="result-title">Results</h2>
                <div className='result-filename'>
                    <strong>檔案名稱:</strong>
                    {editedResults[currentIndex] && editedResults[currentIndex].originalFilename ? (
                        <div>{editedResults[currentIndex] && editedResults[currentIndex].originalFilename}</div>
                    ) : (<div>{editedResults[currentIndex] && editedResults[currentIndex].filename}</div>)}
                </div>
                <div className="result-content">
                    <div className="result-image-container">
                        <button onClick={handlePrevImage}>&lt;</button>
                        <div className="result-image">
                            {editedResults[currentIndex] && editedResults[currentIndex].status === 'error' ? (
                                <div className="result-error-message">圖像辨識錯誤</div>
                            ) : (
                                <img src={`http://localhost:5000/uploads/${results[currentIndex]?.filename}`} alt="Preview" />
                            )}
                        </div>
                        <button onClick={handleNextImage}>&gt;</button>
                    </div>
                    <div className="result-text-container">
                        {renderContent()}
                    </div>
                </div>
                <div className="result-info">
                    <div>張數：{currentIndex + 1}/{editedResults.length}</div>
                </div>
                <div className="success-result">成功：{successResult} 張</div>
                <div className="error-result">失敗：{errorResult} 張</div>
                <div className="result-buttons"></div>
                {successResult > 0 ? (
                    <button className="save-all" onClick={handleSaveAllClick}>全部保存</button>
                ) : (
                    <button className="save-all" onClick={() => navigate('/upload')}>重新上傳</button>
                )}
            </div>
        </div>
    );
};

export default Result;
