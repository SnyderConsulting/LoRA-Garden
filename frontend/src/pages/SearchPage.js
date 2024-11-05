import React, { useState, useEffect } from 'react';
import {
    Grid,
    Input,
    IconButton,
    HStack,
    useToast,
} from '@chakra-ui/react';
import { SearchIcon } from '@chakra-ui/icons';
import axios from 'axios';
import ModelCard from '../components/ModelCard';

function SearchPage() {
    const [models, setModels] = useState([]);
    const [containers, setContainers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const toast = useToast();

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
            toast({
                title: 'Error fetching models',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    const fetchContainers = async () => {
        try {
            const response = await axios.get('http://localhost:8000/garden');
            setContainers(response.data.containers || []);
        } catch (error) {
            console.error('Error fetching containers:', error);
            toast({
                title: 'Error fetching containers',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    useEffect(() => {
        fetchModels();
        fetchContainers();
    }, []);

    const handleSearch = (e) => {
        if (e.key === 'Enter') {
            fetchModels(searchQuery);
        }
    };

    const handleAddToContainer = async (modelId, containerName) => {
        try {
            await axios.post('http://localhost:8000/garden/containers/add-lora', {
                container_name: containerName,
                lora_id: modelId,
            });
            toast({
                title: `Added to ${containerName}!`,
                status: 'success',
                duration: 2000,
                isClosable: true,
            });
            // Refresh containers after adding
            fetchContainers();
        } catch (error) {
            console.error('Error adding LoRA:', error);
            toast({
                title: 'Error adding to container',
                status: 'error',
                duration: 2000,
                isClosable: true,
            });
        }
    };

    return (
        <>
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
                    <ModelCard
                        key={model.id}
                        model={model}
                        containers={containers}
                        onAddToContainer={handleAddToContainer}
                    />
                ))}
            </Grid>
        </>
    );
}

export default SearchPage;