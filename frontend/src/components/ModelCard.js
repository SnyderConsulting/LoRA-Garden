import React, { useState, useEffect } from 'react';
import {
  Box,
  Text,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useToast,
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import axios from 'axios';

const ModelCard = ({ model }) => {
  const { id, name, creatorName, imageUrl } = model;
  const showcaseImageUrl = imageUrl ? imageUrl : 'https://via.placeholder.com/300'
  const [containers, setContainers] = useState([]);
  const toast = useToast();

  useEffect(() => {
    // Fetch the list of containers
    const fetchContainers = async () => {
      try {
        const response = await axios.get('http://localhost:8000/garden');
        setContainers(response.data.containers || []);
      } catch (error) {
        console.error('Error fetching containers:', error);
      }
    };
    fetchContainers();
  }, []);

  const handleAddToContainer = async (containerName) => {
    try {
      await axios.post('http://localhost:8000/garden/containers/add-lora', {
        container_name: containerName,
        lora_id: id,
      });
      toast({
        title: `Added to ${containerName}!`,
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error adding LoRA:', error);
      toast({
        title: 'Error adding to container.',
        status: 'error',
        duration: 2000,
        isClosable: true,
      });
    }
  };

  return (
      <Box
          backgroundImage={`url(${showcaseImageUrl})`}
          backgroundSize="cover"
          backgroundPosition="center"
          borderRadius="md"
          overflow="hidden"
          position="relative"
          height="200px"
          _hover={{ transform: 'scale(1.02)', transition: '0.3s' }}
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
            {name}
          </Text>
          <Text fontSize="sm">{creatorName}</Text>
        </Box>
        <Box position="absolute" top="0" right="0" m={2}>
          <Menu>
            <MenuButton as={Button} rightIcon={<ChevronDownIcon />} size="sm">
              Add to
            </MenuButton>
            <MenuList>
              {containers.map((container) => (
                  <MenuItem
                      key={container.name}
                      onClick={() => handleAddToContainer(container.name)}
                  >
                    {container.name}
                  </MenuItem>
              ))}
            </MenuList>
          </Menu>
        </Box>
      </Box>
  );
};

export default ModelCard;