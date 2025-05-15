import React, { useState, useRef } from 'react';
import { Button, TextField, Box, Typography, CircularProgress, Paper, Alert, Container } from '@mui/material';
import Webcam from 'react-webcam';
import axios from 'axios';

const FaceRegister = () => {
  const [userId, setUserId] = useState('');
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', severity: '' });
  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);

  const captureImage = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImage(imageSrc);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId || !image) {
      setMessage({ text: 'User ID and image are required', severity: 'error' });
      return;
    }

    setLoading(true);
    setMessage({ text: '', severity: '' });

    try {
      // Convert base64 to blob
      const blob = await fetch(image).then(res => res.blob());
      
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('image', blob, 'face.jpg');

      const response = await axios.post('http://localhost:8000/register_face/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setMessage({ text: response.data.message, severity: 'success' });
      setUserId('');
      setImage(null);
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message;
      setMessage({ text: errorMsg, severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          Register New Face
        </Typography>
        
        {message.text && (
          <Alert severity={message.severity} sx={{ mb: 3 }}>
            {message.text}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <TextField
            label="User ID"
            variant="outlined"
            fullWidth
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            margin="normal"
            required
          />

          <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
            Capture or Upload Face Image
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 4 }}>
            <Box sx={{ flex: 1 }}>
              <Webcam
                audio={false}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                videoConstraints={{ facingMode: 'user' }}
                width="100%"
                height="auto"
              />
              <Button
                variant="contained"
                color="primary"
                onClick={captureImage}
                fullWidth
                sx={{ mt: 2 }}
              >
                Capture Image
              </Button>
            </Box>

            <Box sx={{ flex: 1 }}>
              {image ? (
                <img
                  src={image}
                  alt="Captured"
                  style={{ width: '100%', height: 'auto', borderRadius: '4px' }}
                />
              ) : (
                <Box
                  sx={{
                    border: '2px dashed grey',
                    borderRadius: '4px',
                    p: 4,
                    textAlign: 'center',
                  }}
                >
                  <Typography>No image selected</Typography>
                </Box>
              )}
              <Button
                variant="outlined"
                color="primary"
                onClick={() => fileInputRef.current.click()}
                fullWidth
                sx={{ mt: 2 }}
              >
                Upload Image
              </Button>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                style={{ display: 'none' }}
              />
            </Box>
          </Box>

          <Button
            type="submit"
            variant="contained"
            color="secondary"
            fullWidth
            size="large"
            sx={{ mt: 4 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Register Face'}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default FaceRegister;