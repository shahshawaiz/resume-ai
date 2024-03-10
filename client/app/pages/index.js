// pages/index.js or pages/home.js
import Head from 'next/head';
import { useState } from 'react';
import { FileUploader } from '../components/FileUploader';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import styles from '../styles/Home.module.css';

export default function Home() {
  const [files, setFiles] = useState([]);

  const onSuccess = (savedFiles) => {
    setFiles(savedFiles);
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>Upload and Generate</title>
      </Head>
      <div>    
    </div>
      <FileUploader onSuccess={onSuccess} />
      <ToastContainer />
      <footer className={styles.footer}>
      <div className={styles.footerContent}>
        <span>Developed by Shawaiz Shah</span>
        <a href="https://www.linkedin.com/in/shawaiz-shah-32b40537" target="_blank" rel="noopener noreferrer">
          <img src="/linkedin.png" alt="LinkedIn" className={styles.icon} /> LinkedIn
        </a>
        <a href="https://twitter.com/shasaheb" target="_blank" rel="noopener noreferrer">
          <img src="/x.png" alt="X" className={styles.icon} /> X
        </a>        
        <a href="https://py.pl/1YzFeh" target="_blank" rel="noopener noreferrer">
          <img src="/buy-me-a-coffee.png" alt="Buy Me a Coffee" className={styles.icon} /> Buy Me a Coffee
        </a>
      </div>
    </footer>
    </div>
  );
}
