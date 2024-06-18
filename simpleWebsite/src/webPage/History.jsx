import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import Navbar from '../components/Navbar';
import '../css/history.css';
import { AuthContext } from "../components/AuthContext";

export default function History() {
    const [files, setFiles] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [filesPerPage] = useState(5);
    const navigate = useNavigate();
    const [isEditing, setIsEditing] = useState([]);
    const { isLoggedIn, authChecked } = useContext(AuthContext);
    const [status, setStatus] = useState('');

    useEffect(() => {
        if (authChecked && !isLoggedIn) {
            alert("Please log in to view your upload history.");
            navigate("/login");
        }
    }, [isLoggedIn, authChecked, navigate]);

    useEffect(() => {
        const fetchHistory = async () => {
            axios.get('http://localhost:5000/history', { withCredentials: true })
                .then(response => {
                    setFiles(response.data.files);
                    setIsEditing(Array(response.data.files.length).fill(false));
                })
                .catch(error => {
                    if (error.response && error.response.status === 401) {
                        navigate("/login");
                    } else if (error.response && error.response.status === 500) {
                        console.error('Server error:', error.response.data);
                        setStatus('Server error. Please try again later.');
                    } else {
                        console.error('Error fetching history:', error);
                        setStatus('Server error. Please try again later.');
                    }
                });
        };

        fetchHistory();
    }, [navigate]);

    const handleEditClick = (index) => {
        const updatedIsEditing = [...isEditing];
        updatedIsEditing[index] = true;
        setIsEditing(updatedIsEditing);
    };

    const handleDownloadClick = (index) => {
        const file = files[index];
        const result = file.result;
        const blob = new Blob([result], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = (file.originalFilename).split('.').slice(0, -1).join('.') + '.txt';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleSaveClick = (index) => {
        const file = files[index];
        axios.put(`http://localhost:5000/saveHistoryResult/${file._id}`,
            { result: file.result }, { withCredentials: true })
            .then(response => {
                console.log('Result updated successfully:', response.data);
                const updatedEditing = [...isEditing];
                updatedEditing[index] = false;
                setIsEditing(updatedEditing);
            })
            .catch(error => {
                if (error.response && error.response.status === 401) {
                    console.error('Unauthorized:', error.response.data);
                } else if (error.response && error.response.status === 500) {
                    console.error('Server error:', error.response.data);
                } else {
                    console.error('Error updating result:', error);
                }
            });
    };

    const handleCancelClick = (index) => {
        const updatedIsEditing = [...isEditing];
        updatedIsEditing[index] = false;
        setIsEditing(updatedIsEditing);
    };

    const handleChangePage = (pageNumber) => {
        setCurrentPage(pageNumber);
    };

    const handlePreviousPage = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1);
        }
    };

    const handleNextPage = () => {
        if (currentPage < Math.ceil(files.length / filesPerPage)) {
            setCurrentPage(currentPage + 1);
        }
    };

    // Get current files
    const indexOfLastFile = currentPage * filesPerPage;
    const indexOfFirstFile = indexOfLastFile - filesPerPage;
    const currentFiles = files.slice(indexOfFirstFile, indexOfLastFile);

    // Page numbers
    const pageNumbers = [];
    for (let i = 1; i <= Math.ceil(files.length / filesPerPage); i++) {
        pageNumbers.push(i);
    }

    return (
        <div className="history-page">
            <Navbar />
            <div className="history-container list-container">
                <h2 className="history-title">Upload History</h2>
                {files.length === 0 ? (
                    <>
                        {status ? (
                            <p>{status}</p>
                        ) : (
                            <p>No uploads found.</p>
                        )}
                    </>
                ) : (
                    <>
                        <ul className="file-list">
                            {currentFiles.map((file, index) => (
                                <li key={index} className="file-item">
                                    <div className="file-preview">
                                        <div className="file-info">
                                            <strong>Filename:</strong>
                                            {file.originalFilename}
                                        </div>
                                        <div className="image-container">
                                            <img src={`http://localhost:5000/uploads/${file.filename}`} alt={file.filename}
                                                className="preview-image" />
                                        </div>
                                        <div className="file-info">
                                            <strong>Upload Date:</strong>
                                            {new Date(file.uploadDate).toLocaleString()}
                                        </div>
                                    </div>
                                    <div className="history-text-container">
                                        <strong>Result:</strong>
                                        {isEditing[indexOfFirstFile + index] ? (
                                            <>
                                                <textarea
                                                    value={file.result}
                                                    onChange={(event) => {
                                                        const updatedFiles = [...files];
                                                        updatedFiles[indexOfFirstFile + index].result = event.target.value;
                                                        setFiles(updatedFiles);
                                                    }}
                                                />
                                                <button onClick={() => handleSaveClick(indexOfFirstFile + index)} className="save">Save</button>
                                                <button onClick={() => handleCancelClick(indexOfFirstFile + index)} className="cancel">Cancel</button>
                                            </>
                                        ) : (
                                            <>
                                                <div className="show-text-container">
                                                    {file.result}
                                                </div>
                                                <div className="history-buttons">
                                                    <button onClick={() => handleEditClick(indexOfFirstFile + index)} className="edit">Edit</button>
                                                    <button onClick={() => handleDownloadClick(indexOfFirstFile + index)} className="download">Download</button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                </li>
                            ))}
                        </ul>
                        {files.length > 5 && (
                            <div className="pagination">
                                <button onClick={handlePreviousPage} disabled={currentPage === 1}>Previous</button>
                                {pageNumbers.map(number => (
                                    <button key={number} onClick={() => handleChangePage(number)}>
                                        {number}
                                    </button>
                                ))}
                                <button onClick={handleNextPage} disabled={currentPage === pageNumbers.length}>Next</button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
