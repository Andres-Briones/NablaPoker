class Node:
    def __init__(self, data, position: int):
        self.data = data 
        self.position = position
        self.next = None
        self.prev = None

class CircularLinkedList:
    def __init__(self):
        self.head = None # The head is always the node with the smallest position
        self.len = 0

    def append(self, position: int, data):
        # Create a new node with the given player
        new_node = Node(data, position)
        
        # If the list is empty, initialize it with the new node
        if not self.head:
            # The new node points to itself, forming a single-node circular list
            self.head = new_node
            self.head.next = self.head
            self.head.prev = self.head
        else:
            current = self.head
            # Loop while the position of current is smaller the the new_node position
            while current.position < position:
                current = current.next
                if current == self.head :
                    break
            # Now either current.position >= position or current = head and the new node should be playced last. 
            # In either caese we need to place the new_node before just before current. 

            # If there is already a node with the same position, raise an error
            if current.position == position :  
                raise Exception("There is already and element at that position")
                return 

            # Insert the new node between current.prev and current
            new_node.next = current
            new_node.prev = current.prev
            current.prev = new_node
            new_node.prev.next = new_node

            # If the new node has the smallest position, update the head
            if new_node.position < self.head.position:
                self.head = new_node
        
        self.len += 1

    def remove(self, position: int):
        current = self.head
        while True:
            if current.position == position:
                self.len -= 1 
                # If the list had only one node, set the head to None
                if current == self.head and current.next == self.head:
                    self.head = None
                else:
                    current.prev.next = current.next
                    current.next.prev = current.prev
                    # If the removed node is the head, set the head to the next node
                    if current == self.head:
                        self.head = current.next
                break
            current = current.next

            # If the we got back to head, it means that there wasn't a node with the given position
            if current == self.head:
                raise Exception("There isn't an element at that position")
                break

    # Get the next element after the given position. The position doesn't have to be in the list
    def get_next(self, position: int, skip: int = 0):
        current = self.head
        while current.position <= position:
            current = current.next
            # If we go back to self, it means that the given position is higher than the highest position, in that case return the head
            if current == self.head:
                return self.head.data

        if skip: 
            for _ in range(skip):
                current = current.next

        return current.data

    def get_index(self, position: int) -> int:
        '''Return the index of the node at the given position'''
        index = 0
        current = self.head
        while current.position != position:
            index += 1
            current = current.next
            if current == self.head:
                raise Exception("There isn't an element at that position")
                break
        return index
    
    # Returns a python list with the elements of the circular list
    def iterator(self):
        current = self.head
        while True:
            yield current.data
            current = current.next
            if current == self.head:
                break


    def __str__(self):
        current = self.head
        strings = ["--------------------\n"]
        if current is None: 
            print("Empty")
        else :
            while True :
                strings.append(f"Position {current.position}: {current.data}\n")
                current = current.next
                if current == self.head:
                    break
        strings.append("--------------------")
        string = "\n".join(strings)
        return string

    def __iter__(self):
        if not self.head:
            return
        current = self.head
        while True:
            yield current.data
            current = current.next
            if current == self.head:
                break

    def __len__(self):
        return self.len
    
    def __getitem__(self, position: int):
        current = self.head
        while current.position != position : 
            current = current.next
            # If the we got back to head, it means that there wasn't a node with the given position
            if current == self.head:
                raise Exception("There isn't an element at that position")
                break
        return current.data

    def get(self, position: int, default = None):
        try:
            data = self.__getitem__(position)
        except Exception:
            return default 
        return data

    def __setitem__(self, position: int, data) :
        return self.append(position, data)

    # Get the list of the positions of the elements in the circular list
    def positions(self):
        current = self.head
        positions = []
        while True:
            positions.append(current.position)
            current = current.next
            if current == self.head:
                break
        return positions

    def to_list(self):
        data_list = []
        for data in self:
            data_list.append(data)
        return data_list
