import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Container,
  Input,
  Heading,
  IconButton,
  HStack,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import axios from 'axios';
import ModelCard from './components/ModelCard';

function App() {
  const [models, setModels] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchModels = async (query) => {
    try {
      const response = await axios.get('http://localhost:8000/models', {
        params: {
          query: query || undefined,
          limit: 20,
        },
      });
      setModels(response.data.models);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      fetchModels(searchQuery);
    }
  };

  return (
    <Container maxW="container.xl" py={5}>
      <Heading mb={6}>Model Search</Heading>
      <HStack mb={6}>
        <Input
          type="text"
          placeholder="Search for models..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleSearch}
        />
        <IconButton
          icon={<SearchIcon />}
          onClick={() => fetchModels(searchQuery)}
          aria-label="Search"
        />
      </HStack>
      <Grid templateColumns="repeat(auto-fill, minmax(250px, 1fr))" gap={6}>
        {models.map((model) => (
          <ModelCard key={model.id} model={model} />
        ))}
      </Grid>
    </Container>
  );
}

export default App;
