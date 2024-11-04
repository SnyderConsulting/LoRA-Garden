import React from 'react';
import { Box, Text, Badge } from '@chakra-ui/react';

const ModelCard = ({ model }) => {
  const { name, creatorName, imageUrl } = model;

  return (
    <Box
      backgroundImage={`url(${imageUrl || 'https://via.placeholder.com/300'})`}
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
    </Box>
  );
};

export default ModelCard;
