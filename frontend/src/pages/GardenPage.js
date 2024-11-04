import React, { useState, useEffect } from 'react';
import {
    Container,
    Heading,
    Box,
    Input,
    Button,
    VStack,
    HStack,
    Text,
    Grid,
} from '@chakra-ui/react';
import axios from 'axios';
import ModelCard from '../components/ModelCard';

const GardenPage = () => {
    const [garden, setGarden] = useState(null);
    const [containerName, setContainerName] = useState('');

    const fetchGarden = async () => {
        try {
            const response = await axios.get('http://localhost:8000/garden');
            setGarden(response.data);
        } catch (error) {
            console.error('Error fetching garden:', error);
        }
    };

    useEffect(() => {
        fetchGarden();
    }, []);

    const createContainer = async () => {
        if (!containerName) return;

        try {
            await axios.post('http://localhost:8000/garden/containers', {
                name: containerName,
            });
            setContainerName('');
            fetchGarden();
        } catch (error) {
            console.error('Error creating container:', error);
        }
    };

    return (
        <div>
            <Heading mb={6}>My Garden</Heading>
            <HStack mb={6}>
                <Input
                    placeholder="Container name"
                    value={containerName}
                    onChange={(e) => setContainerName(e.target.value)}
                />
                <Button onClick={createContainer}>Add Container</Button>
            </HStack>
            {garden && garden.containers.length > 0 ? (
                garden.containers.map((container) => (
                    <Box key={container.name} mb={6}>
                        <Heading size="md" mb={4}>{container.name}</Heading>
                        {container.loRAs.length > 0 ? (
                            <Grid templateColumns="repeat(auto-fill, minmax(250px, 1fr))" gap={6}>
                                {container.loRAs.map((loraId) => (
                                    <LoRACard
                                        key={loraId}
                                        loraId={loraId}
                                        containerName={container.name}
                                        fetchGarden={fetchGarden}
                                    />
                                ))}
                            </Grid>
                        ) : (
                            <Text>No LoRAs in this container.</Text>
                        )}
                    </Box>
                ))
            ) : (
                <Text>No containers in your garden. Add one above!</Text>
            )}
        </div>
    );
};

const LoRACard = ({ loraId, containerName, fetchGarden }) => {
    const [model, setModel] = useState(null);

    useEffect(() => {
        const fetchModel = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/models/${loraId}`);
                setModel(response.data);
            } catch (error) {
                console.error('Error fetching model:', error);
            }
        };
        fetchModel();
    }, [loraId]);

    const removeFromContainer = async () => {
        try {
            await axios.post('http://localhost:8000/garden/containers/remove-lora', {
                container_name: containerName,
                lora_id: loraId,
            });
            fetchGarden();
        } catch (error) {
            console.error('Error removing LoRA:', error);
        }
    };

    if (!model) return null;

    return (
        <Box
            backgroundImage={`url(${model.imageUrl || 'https://via.placeholder.com/300'})`}
            backgroundSize="cover"
            backgroundPosition="center"
            borderRadius="md"
            overflow="hidden"
            position="relative"
            height="200px"
        >
            <Box
                position="absolute"
                bottom="0"
                width="100%"
                bg="rgba(0, 0, 0, 0.6)"
                color="white"
                py={2}
                px={3}
            >
                <Text fontWeight="bold" fontSize="lg">
                    {model.name}
                </Text>
                <Text fontSize="sm">{model.creatorName}</Text>
            </Box>
            <Box position="absolute" top="0" right="0" m={2}>
                <Button size="sm" onClick={removeFromContainer}>
                    Remove
                </Button>
            </Box>
        </Box>
    );
};

export default GardenPage;