import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  CircularProgress,
  Typography,
  LinearProgress,
  Alert,
  Paper
} from '@mui/material';
import Webcam from 'react-webcam';
import axios from 'axios';

const FaceSearch = () => {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const webcamRef = React.useRef(null);
  const fileInputRef = React.useRef(null);

  const captureImage = () => {
    const imageSrc = webcamRef.current.getScreenshot();
    setImage(imageSrc);
    setResult(null);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setImage(event.target.result);
        setResult(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSearch = async () => {
    if (!image) {
      setError('Veuillez capturer ou uploader une image');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const blob = await fetch(image).then(res => res.blob());
      const formData = new FormData();
      formData.append('image', blob, 'search.jpg');

      const response = await axios.post('http://localhost:8000/search_face/', formData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  const getPercentageColor = (percentage) => {
    console.log("pourcentage : ",percentage)
    if (percentage < 65) return 'error';
    if (percentage < 80) return 'warning';
    return 'success';
  };

  return (
    <Paper elevation={3} sx={{ p: 2, mt: 2 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 1, fontSize: '1.1rem' }}>
        Reconnaissance Faciale
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        {/* Colonne Webcam */}
        <Box sx={{ flex: 1 }}>
          <Webcam
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={{ facingMode: 'user' }}
            style={{ 
              width: '100%',
              borderRadius: '4px',
              height: '350px',
              objectFit: 'cover'
            }}
          />
          <Button
            variant="contained"
            fullWidth
            onClick={captureImage}
            sx={{ 
              mt: 1,
              py: 0.5,
              fontSize: '0.75rem'
            }}
            size="small"
          >
            Capturer
          </Button>
        </Box>

        {/* Colonne Image */}
        <Box sx={{ flex: 1 }}>
          {image ? (
            <img
              src={image}
              alt="Captured"
              style={{ 
                width: '100%',
                height: '180',
                heightMax:'180px',
                objectFit: 'cover',
                borderRadius: '4px'
              }}
            />
          ) : (
            <Box
              sx={{
                border: '1px dashed #ccc',
                borderRadius: '4px',
                height: '350px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: '#f5f5f5'
              }}
            >
              <Typography variant="caption" color="text.secondary">
                Aperçu
              </Typography>
            </Box>
          )}
          <Button
            variant="outlined"
            fullWidth
            onClick={() => fileInputRef.current.click()}
            sx={{ 
              mt: 1,
              py: 0.5,
              fontSize: '0.75rem'
            }}
            size="small"
          >
            Uploader
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
        variant="contained"
        color="primary"
        fullWidth
        sx={{ 
          py: 0.6,
          fontSize: '0.75rem',
          mb: 1
        }}
        onClick={handleSearch}
        disabled={loading || !image}
        size="small"
      >
        {loading ? <CircularProgress size={16} /> : 'Rechercher'}
      </Button>

      {error && (
        <Alert severity="error" sx={{ py: 0.5, fontSize: '0.75rem' }}>
          {error}
        </Alert>
      )}

      {result && (
        <Card sx={{ mt: 1, borderRadius: '4px' }}>
          <CardContent sx={{ p: 1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              Résultats
            </Typography>

            {result.success ? (
              <>
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  <strong>{result.user_id}</strong>
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={result.percentage}
                    color={getPercentageColor(result.percentage)}
                    sx={{ 
                      height: 6, 
                      flexGrow: 1,
                      borderRadius: '3px'
                    }}
                  />
                  <Typography variant="caption" sx={{ minWidth: '30px' }}>
                    {result.percentage}%
                  </Typography>
                </Box>

                <Box sx={{ display: 'flex', mt: 0.5 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
                    Dist: {result.distance.toFixed(2)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
                    Seuil: {result.threshold.toFixed(2)}
                  </Typography>
                </Box>
              </>
            ) : (
              <>
                <Typography variant="body2" color="error" sx={{ mb: 0.5 }}>
                  Non reconnu
                </Typography>
                {result.percentage > 0 && (
                  <>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={result.percentage}
                        color={getPercentageColor(result.percentage)}
                        sx={{ 
                          height: 6,
                          flexGrow: 1,
                          borderRadius: '3px'
                        }}
                      />
                      <Typography variant="caption" sx={{ minWidth: '30px' }}>
                        {result.percentage}%
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      (seuil à 65%)
                    </Typography>
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Paper>
  );
};

export default FaceSearch;