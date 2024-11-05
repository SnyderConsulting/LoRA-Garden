import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ChakraProvider, Container, HStack, Button } from '@chakra-ui/react';
import ContainerDetailPage from './pages/ContainerDetailPage';
import SearchPage from './pages/SearchPage';
import GardenPage from './pages/GardenPage';

function App() {
  return (
      <ChakraProvider>
        <Router>
          <Container maxW="container.xl" py={5}>
            <HStack mb={6} spacing={4}>
              <Link to="/">
                <Button>Search</Button>
              </Link>
              <Link to="/garden">
                <Button>My Garden</Button>
              </Link>
            </HStack>
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/garden" element={<GardenPage />} />
              <Route path="/garden/:containerName" element={<ContainerDetailPage />} />
            </Routes>
          </Container>
        </Router>
      </ChakraProvider>
  );
}

export default App;