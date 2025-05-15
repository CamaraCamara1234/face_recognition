import { createGlobalStyle } from 'styled-components';

export const GlobalStyles = createGlobalStyle`
  body {
    margin: 0;
    padding: 0;
    background-color: ${({ theme }) => theme.palette.background.default};
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 24px;
    margin-bottom: 24px;
  }

  .section-title {
    color: ${({ theme }) => theme.palette.primary.main};
    margin-bottom: 24px;
  }
`;