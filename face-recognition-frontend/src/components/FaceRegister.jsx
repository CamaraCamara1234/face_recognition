import React, { useState, useRef, useEffect } from 'react';
import { 
  Button, 
  TextField, 
  Box, 
  Typography, 
  CircularProgress, 
  Paper, 
  Alert, 
  Container,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import Webcam from 'react-webcam';
import axios from 'axios';

const FaceRegister = () => {
  const [userId, setUserId] = useState('');
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', severity: '' });
  const [tabValue, setTabValue] = useState(0);
  const [userExists, setUserExists] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
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

  const checkUserExists = async () => {
    if (!userId) return;
    
    try {
      const response = await axios.get(`http://localhost:8000/user_exists/?user_id=${userId}`);
      setUserExists(response.data.exists);
    } catch (error) {
      console.error("Error checking user existence:", error);
      setUserExists(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (userId) {
        checkUserExists();
      }
    }, 500);

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!userId || !image) {
      setMessage({ text: 'User ID and image are required', severity: 'error' });
      return;
    }

    if (userExists && tabValue === 0) {
      setConfirmOpen(true);
      return;
    }

    await processSubmission();
  };

  const processSubmission = async () => {
    setLoading(true);
    setMessage({ text: '', severity: '' });

    try {
      const blob = await fetch(image).then(res => res.blob());
      const formData = new FormData();
      formData.append('user_id', userId);
      formData.append('image', blob, 'face.jpg');

      const endpoint = userExists ? 'update_face/' : 'register_face/';
      const response = await axios.post(
        `http://localhost:8000/${endpoint}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setMessage({ 
        text: response.data.message, 
        severity: 'success',
        details: userExists ? 'User face updated successfully' : 'New user registered successfully'
      });
      
      if (!userExists) {
        setUserId('');
        setImage(null);
      }
      setUserExists(true);
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message;
      setMessage({ 
        text: errorMsg, 
        severity: 'error',
        details: error.response?.data?.error || ''
      });
    } finally {
      setLoading(false);
      setConfirmOpen(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setUserId('');
    setImage(null);
    setUserExists(false);
    setMessage({ text: '', severity: '' });
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Tabs value={tabValue} onChange={handleTabChange} centered sx={{ mb: 3 }}>
          <Tab label="Register New Face" />
          <Tab label="Update Existing Face" />
        </Tabs>

        {message.text && (
          <Alert severity={message.severity} sx={{ mb: 3 }}>
            <Typography>{message.text}</Typography>
            {message.details && <Typography variant="body2">{message.details}</Typography>}
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
            helperText={
              userExists && tabValue === 0 
                ? 'This user already exists. Submitting will update their face data.'
                : userExists && tabValue === 1
                ? 'User found. Upload new face image to update.'
                : !userExists && tabValue === 1
                ? 'User not found. Please check the ID or register as new user.'
                : ''
            }
          />

          <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
            {tabValue === 0 ? 'Capture or Upload Face Image' : 'Capture or Upload New Face Image'}
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
            disabled={loading || (tabValue === 1 && !userExists)}
          >
            {loading ? (
              <CircularProgress size={24} />
            ) : tabValue === 0 ? (
              userExists ? 'Update Existing User' : 'Register New User'
            ) : (
              'Update User Face'
            )}
          </Button>
        </Box>
      </Paper>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>Confirm User Update</DialogTitle>
        <DialogContent>
          <Typography>
            User "{userId}" already exists. Do you want to update their face data?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button onClick={processSubmission} color="primary" autoFocus>
            Confirm Update
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default FaceRegister;