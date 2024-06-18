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
    const [editedResults, setEditedResults] = useState(results.map(result => ({ ...result, data: '' })));
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

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

    useEffect(() => {
        const fetchResults = async () => {
            setLoading(true);
            try {
                const fetchedResults = await Promise.all(
                    results.map(async (result) => {
                        if (result.status === 'success') {
                            const response = await axios.get(`http://localhost:5000/results/${result.filename}`, { withCredentials: true });
                            console.log('Response:', { ...result, data: response.data.data });
                            return { ...result, data: response.data.data };
                        }
                        return result;
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
    }, [results]);

    const handleEditClick = () => {
        setIsEditing(true);
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
                    console.log('Results saved successfully:', response.data);
                    navigate('/history');
                })
                .catch(error => {
                    console.error('Error saving results:', error);
                });
        }
    };

    return (
        <div className="result-page list-container">
            <Navbar />
            <div className="result-container">
                <h2 className="result-title">Results</h2>
                <div className='result-filename'>
                    檔案名稱:
                    <div>
                        {editedResults[currentIndex].status === 'error'
                            ? (editedResults[currentIndex].filename)
                            : (editedResults[currentIndex].filename?.split('-').slice(1).join('-'))}
                    </div>
                </div>
                <div className="result-content">
                    <div className="result-image-container">
                        <button onClick={handlePrevImage}>&lt;</button>
                        <div className="result-image">
                            {editedResults[currentIndex].status === 'error' ? (
                                <div className="result-error-message">圖像辨識錯誤</div>
                            ) : (
                                <img src={`http://localhost:5000/uploads/${results[currentIndex]?.filename}`} alt="Preview" />
                            )}
                        </div>
                        <button onClick={handleNextImage}>&gt;</button>
                    </div>
                    <div className="result-text-container">
                        {loading ? (
                            <div className="loading-spinner">loading...</div>
                        ) : (
                            isEditing ? (
                                <div>
                                    <textarea
                                        value={editedResults[currentIndex].data}
                                        onChange={(event) => {
                                            const updatedResults = [...editedResults];
                                            updatedResults[currentIndex].data = event.target.value;
                                            setEditedResults(updatedResults);
                                        }}
                                    />
                                    <button className="save" onClick={handleSaveClick}>保存</button>
                                    <button className="cancel" onClick={handleCancelClick}>取消</button>
                                </div>
                            ) : (
                                <div>
                                    {editedResults[currentIndex].status === 'error' ? (
                                        <div className="show-text-container-error">原因：{editedResults[currentIndex].data}</div>
                                    )
                                        : (
                                            <>
                                                <div className="show-text-container">{editedResults[currentIndex].data}</div>
                                                <button className="edit" onClick={handleEditClick}>修改</button>
                                            </>
                                        )
                                    }
                                </div>
                            )
                        )}
                    </div>
                </div>
                <div className="result-info">
                    <div>張數：{currentIndex + 1}/{editedResults.length}</div>
                </div>
                <button className="save-all" onClick={handleSaveAllClick}>全部保存</button>
            </div>
        </div>
    );
};

export default Result;
