import { useState } from 'react';
import {
    AlertDialog,
    AlertDialogBody,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogContent,
    AlertDialogOverlay,
    Button,
    IconButton,
    useToast
} from '@chakra-ui/react';
import { DeleteIcon } from '@chakra-ui/icons';
import axios from 'axios';

const DeleteContainerDialog = ({ containerName, onDelete }) => {
    const [isOpen, setIsOpen] = useState(false);
    const toast = useToast();

    const handleDelete = async () => {
        try {
            await axios.delete('http://localhost:8000/garden/containers', {
                data: { container_name: containerName }
            });

            toast({
                title: 'Container deleted',
                status: 'success',
                duration: 2000,
                isClosable: true,
            });

            onDelete();
            setIsOpen(false);
        } catch (error) {
            toast({
                title: 'Error deleting container',
                description: error.response?.data?.detail || 'An error occurred',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    return (
        <>
            <IconButton
                icon={<DeleteIcon />}
                colorScheme="red"
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(true)}
                aria-label="Delete container"
            />

            <AlertDialog
                isOpen={isOpen}
                onClose={() => setIsOpen(false)}
            >
                <AlertDialogOverlay>
                    <AlertDialogContent>
                        <AlertDialogHeader>Delete Container</AlertDialogHeader>
                        <AlertDialogBody>
                            Are you sure you want to delete "{containerName}"? This action cannot be undone.
                        </AlertDialogBody>
                        <AlertDialogFooter>
                            <Button onClick={() => setIsOpen(false)}>
                                Cancel
                            </Button>
                            <Button colorScheme="red" ml={3} onClick={handleDelete}>
                                Delete
                            </Button>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialogOverlay>
            </AlertDialog>
        </>
    );
};

export default DeleteContainerDialog;