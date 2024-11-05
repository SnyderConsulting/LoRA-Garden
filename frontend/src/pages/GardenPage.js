import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
    useToast,
} from '@chakra-ui/react';
import axios from 'axios';
import DeleteContainerDialog from '../components/DeleteContainerDialog';

const LoRACard = ({ model, containerName, fetchGarden }) => {
    const toast = useToast();

    // Early return if model is undefined
    if (!model) {
        return null;
    }

    const removeFromContainer = async () => {
        try {
            await axios.post('http://localhost:8000/garden/containers/remove-lora', {
                container_name: containerName,
                lora_id: model.id,
            });
            fetchGarden();
            toast({
                title: 'LoRA removed successfully',
                status: 'success',
                duration: 2000,
                isClosable: true,
            });
        } catch (error) {
            console.error('Error removing LoRA:', error);
            toast({
                title: 'Error removing LoRA',
                status: 'error',
                duration: 2000,
                isClosable: true,
            });
        }
    };

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

const GardenPage = () => {
    const [garden, setGarden] = useState(null);
    const [containerName, setContainerName] = useState('');
    const toast = useToast();

    const fetchGarden = async () => {
        try {
            const response = await axios.get('http://localhost:8000/garden');
            setGarden(response.data);
        } catch (error) {
            console.error('Error fetching garden:', error);
            toast({
                title: 'Error fetching garden',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
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
            toast({
                title: 'Container created successfully',
                status: 'success',
                duration: 2000,
                isClosable: true,
            });
        } catch (error) {
            console.error('Error creating container:', error);
            toast({
                title: 'Error creating container',
                status: 'error',
                duration: 2000,
                isClosable: true,
            });
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
                        <HStack justify="space-between" align="center" mb={4}>
                            <Link to={`/garden/${encodeURIComponent(container.name)}`}>
                                <Heading size="md" _hover={{ textDecoration: 'underline' }}>
                                    {container.name}
                                </Heading>
                            </Link>
                            <DeleteContainerDialog
                                containerName={container.name}
                                onDelete={fetchGarden}
                            />
                        </HStack>
                        {container.loRAs.length > 0 ? (
                            <Grid templateColumns="repeat(auto-fill, minmax(250px, 1fr))" gap={6}>
                                {container.loRAs.map((loraId) => {
                                    const modelDetails = container.modelDetails[String(loraId)];
                                    // Only render if we have the model details
                                    return modelDetails ? (
                                        <LoRACard
                                            key={loraId}
                                            model={modelDetails}
                                            containerName={container.name}
                                            fetchGarden={fetchGarden}
                                        />
                                    ) : null;
                                })}
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

export default GardenPage;