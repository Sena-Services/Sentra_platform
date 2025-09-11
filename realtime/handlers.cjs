module.exports = function(socket) {
    console.log(`CRM Realtime handler initialized for user: ${socket.user}, site: ${socket.site_name}`);
    
    // Join the 'all' room to receive broadcast messages
    socket.join('all');
    
    // Join user-specific room
    if (socket.user && socket.user !== 'Guest') {
        socket.join(socket.user);
        console.log(`User ${socket.user} joined their personal room`);
    }
    
    // Handle room join requests
    socket.on('join', (data) => {
        if (data.rooms && Array.isArray(data.rooms)) {
            data.rooms.forEach(room => {
                socket.join(room);
                console.log(`Socket ${socket.id} joined room: ${room}`);
            });
        }
    });
    
    // Log when client disconnects
    socket.on('disconnect', () => {
        console.log(`Socket ${socket.id} disconnected (user: ${socket.user})`);
    });
    
    // Echo test event for debugging
    socket.on('test_echo', (data) => {
        console.log('Test echo received:', data);
        socket.emit('test_echo_response', { 
            message: 'Echo successful', 
            original: data,
            user: socket.user,
            timestamp: new Date().toISOString()
        });
    });
};