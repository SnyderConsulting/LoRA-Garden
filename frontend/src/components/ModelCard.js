import React from 'react';
import {
  Box,
  Text,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';

const ModelCard = ({ model, containers, onAddToContainer }) => {
  const { id, name, creatorName, imageUrl } = model;
  const showcaseImageUrl = imageUrl ? imageUrl : 'https://via.placeholder.com/300';

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
                      onClick={() => onAddToContainer(id, container.name)}
                  >
                    {container.name}
                  </MenuItem>
              ))}
              {containers.length === 0 && (
                  <MenuItem
                      key={"empty"}
                      onClick={() => {}}
                  >
                    No Containers Found
                  </MenuItem>
              )}
            </MenuList>
          </Menu>
        </Box>
      </Box>
  );
};

export default ModelCard;