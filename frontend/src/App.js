import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ChakraProvider, Container, HStack, Button, Image, Flex } from '@chakra-ui/react';
import ContainerDetailPage from './pages/ContainerDetailPage';
import SearchPage from './pages/SearchPage';
import GardenPage from './pages/GardenPage';

function App() {
  return (
      <ChakraProvider>
        <Router>
          <Container maxW="container.xl" py={5}>
            <Flex align="end" mb={6} gap={4}>
              <Link to="/">
                <Image
                    src="/lora_garden_logo.png"
                    alt="LoRA Garden Logo"
                    height="250px"
                    objectFit="contain"
                    mr={4}
                />
              </Link>
              <HStack spacing={4}>
                <Link to="/">
                  <Button>Search</Button>
                </Link>
                <Link to="/garden">
                  <Button>My Garden</Button>
                </Link>
              </HStack>
            </Flex>
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