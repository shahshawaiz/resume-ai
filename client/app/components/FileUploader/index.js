// Importing necessary dependencies and styles
import { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import styles from './style.module.css'; // Ensure the path is correct
import { Loader } from '../Loader';
import parse from 'html-react-parser';

// FileUploader component definition
export const FileUploader = ({ onSuccess }) => {
  // State hooks for managing component state
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState([]);
  const [jobAdText, setJobAdText] = useState('');
  const [resumeUrl, setResumeUrl] = useState(''); 
  const [resumeDocxUrl, setResumeDocxUrl] = useState(''); // Add this line
  const [coverUrl, setCoverUrl] = useState('');
  const [coverDocxUrl, setCoverDocxUrl] = useState(''); // Add this line
  const [contentCover, setContentCover] = useState('');

  const flaskApiUrl = process.env.NEXT_PUBLIC_FLASK_API_URL;

  // Handles file selection
  const onInputChange = (e) => {
    setFiles(e.target.files);
  };

  // Handles job ad text changes
  const handleJobAdTextChange = (e) => {
    setJobAdText(e.target.value);
  };

  // Handles form submission
  const onSubmit = async (e) => {
    e.preventDefault();

    // Proceed only if files are selected
    if (files.length > 0) {
      try {
        // 
        setLoading(true);

        // Preparing the file for upload
        const formData = new FormData();
        formData.append("file", files[0]);
        
        // Uploading the file
        await axios.post(`${flaskApiUrl}/upload`, formData);
        toast.success('Resume Recevied! (1/2)');
        
        // Preparing data for CV and cover letter generation
        const generateData = new FormData();
        generateData.append('job_ad_text', jobAdText);
        generateData.append("resume_path", `server/docs/${files[0].name}`);

        // Generating CV and cover letter
        const { data } = await axios.post(`${flaskApiUrl}/generate`, generateData);
        
        // Updating state with the URLs and cover letter content
        setResumeUrl(data.resume_url);
        setResumeDocxUrl(data.resume_docx_url);
        setCoverUrl(data.cover_url);
        setCoverDocxUrl(data.cover_docx_url);
        setContentCover(data.cover_letter_text);
        
        toast.success('Your CV and cover letter are ready! (2/2)');
        onSuccess(data);

        setLoading(false);
      } catch (error) {
        toast.error('An error occurred during the file upload or generation process');
        console.error('Error:', error);

        setLoading(false);
      }
    }
  };

  
// Rendering the component UI
return (
  <div className={styles.fileUploaderContainer}>
    <div className={styles.header}>
      <img src="/banner.jpg" alt="Resume Builder Banner" className={styles.bannerImage} />
      <h1 className={styles.bannerTitle}>AI Resume Assistant ✨✨</h1>
      <p className={styles.bannerTagline}>Upload your resume, copy/paste job ad text and get started</p>
    </div>
    {loading && <Loader />}    
    <form onSubmit={onSubmit}>
      <label className={styles.customFileInput}>
        Your resume goes here 
        <input type="file" onChange={onInputChange} className="form-control" multiple style={{ display: 'none' }} />
      </label>
      <textarea
        className={styles.textareaClassNames}
        placeholder="The Job Ad description goes here..."
        value={jobAdText}
        onChange={handleJobAdTextChange}>
      </textarea>
      <button type="submit" className={styles.submitButton}>Submit</button>
    </form>
    {resumeUrl && <a href={`${flaskApiUrl}/download?filename=` + resumeUrl} className={styles.downloadLink} target='_blank' rel="noopener noreferrer" download>Download Improved Resume (PDF)</a>}
    <div className="flex">
      <div>
        {resumeDocxUrl && <a href={`${flaskApiUrl}/download?filename=` + resumeDocxUrl} className={styles.downloadLink} target='_blank' rel="noopener noreferrer" download>Download Improved Resume (Word Document)</a>}
        {coverUrl && <a href={`${flaskApiUrl}/download?filename=` + coverUrl} className={styles.downloadLink} target='_blank' rel="noopener noreferrer" download>Download Cover Letter (PDF)</a>}
      </div>
      <div className="flex-col flex-wrap">
        {coverDocxUrl && <a href={`${flaskApiUrl}/download?filename=` + coverDocxUrl} className={styles.downloadLink} target='_blank' rel="noopener noreferrer" download>Download Optimized Cover Letter (Word Document)</a>}
        {contentCover && <p className={styles.coverLetterContent}>{parse(contentCover)}</p>}
      </div>
    </div>
  </div>
);
};
