import React, {useEffect, useState} from 'react';
import {Box, Button, Checkbox, Grid, Heading, Text, Textarea,} from '@chakra-ui/react';
import {useParams} from 'react-router-dom';
import axios from 'axios';

const ContainerDetailPage = () => {
    const { containerName } = useParams();
    const decodedContainerName = decodeURIComponent(containerName);
    const [loRAs, setLoRAs] = useState([]);
    const [selectedImages, setSelectedImages] = useState({});
    const [promptInput, setPromptInput] = useState('');
    const [outputText, setOutputText] = useState('');

    useEffect(() => {
        const fetchContainerData = async () => {
            try {
                // Fetch the garden data
                const response = await axios.get('http://localhost:8000/garden');
                const garden = response.data;

                // Find the specified container
                const container = garden.containers.find(
                    (c) => c.name === decodedContainerName
                );

                if (!container) {
                    console.error('Container not found');
                    return;
                }

                // Fetch detailed data for each LoRA in the container
                const loRADataPromises = container.loRAs.map((loraId) =>
                    axios.get(`http://localhost:8000/models/${loraId}`)
                );
                const loRAResponses = await Promise.all(loRADataPromises);
                const loRAsData = loRAResponses.map((res) => res.data);

                setLoRAs(loRAsData);
            } catch (error) {
                console.error('Error fetching container data:', error);
            }
        };

        fetchContainerData();
    }, [decodedContainerName]);

    // Handler for image selection
    const handleImageSelect = (modelId, imageUrl, isSelected) => {
        setSelectedImages((prevSelectedImages) => {
            const imagesForModel = prevSelectedImages[modelId] || {};
            if (isSelected) {
                imagesForModel[imageUrl] = true;
            } else {
                delete imagesForModel[imageUrl];
            }
            return {
                ...prevSelectedImages,
                [modelId]: imagesForModel,
            };
        });
    };

    // Handler for generate button
    const handleGenerate = () => {
        // For each selected model
        const outputData = loRAs.map((model) => {
            const selectedModelImages = selectedImages[model.id] || {};
            const selectedImagePrompts = [];

            // For each model version
            model.modelVersions.forEach((version) => {
                // For each image in the version
                version.images.forEach((image) => {
                    if (selectedModelImages[image.url]) {
                        // Get the prompts from image.meta
                        if (image.meta && image.meta.prompt) {
                            selectedImagePrompts.push(image.meta.prompt);
                        }
                    }
                });
            });

            return {
                id: model.id,
                name: model.name,
                description: model.description,
                trainedWords: model.modelVersions.flatMap((version) => version.trainedWords),
                selectedImagePrompts,
            };
        });

        // Output the data
        setOutputText(JSON.stringify(outputData, null, 2));
    };

    return (
        <div>
            <Heading mb={6}>{decodedContainerName}</Heading>

            {/* Display galleries for each LoRA */}
            {loRAs.map((model) => (
                <Box key={model.id} mb={6}>
                    <Heading size="md" mb={4}>{model.name}</Heading>
                    <Text mb={2}>Creator: {model.creatorName}</Text>
                    <Text mb={2}>Description: {model.description}</Text>
                    <Text mb={2}>Trigger Words: {model.trainedWords.join(', ')}</Text>

                    {/* Gallery */}
                    {model.images && model.images.length > 0 ? (
                        <Grid templateColumns="repeat(auto-fill, minmax(150px, 1fr))" gap={4}>
                            {model.images.map((image) => (
                                <Box key={image.url} position="relative">
                                    <img
                                        src={image.url}
                                        alt={`Image for ${model.name}`}
                                        style={{ width: '100%', borderRadius: '4px' }}
                                    />
                                    {image.meta && image.meta.prompt && (
                                        <Text fontSize="xs" mt={1}>
                                            {image.meta.prompt}
                                        </Text>
                                    )}
                                    <Checkbox
                                        position="absolute"
                                        top="2"
                                        left="2"
                                        defaultChecked={false}
                                        onChange={(e) =>
                                            handleImageSelect(model.id, image.url, e.target.checked)
                                        }
                                    />
                                </Box>
                            ))}
                        </Grid>
                    ) : (
                        <Text>No images available for this LoRA.</Text>
                    )}
                </Box>
            ))}

            {/* Prompt input */}
            <Box mt={6}>
                <Textarea
                    placeholder="Enter your prompt here..."
                    value={promptInput}
                    onChange={(e) => setPromptInput(e.target.value)}
                    mb={4}
                />
                <Button onClick={handleGenerate}>Generate</Button>
            </Box>

            {/* Output */}
            {outputText && (
                <Box mt={6}>
                    <Heading size="md" mb={2}>Output</Heading>
                    <Textarea value={outputText} readOnly height="300px"/>
                </Box>
            )}
        </div>
    );
};

export default ContainerDetailPage;