
#define SWAP_UINT32(x) (((x) >> 24) | (((x) & 0x00FF0000) >> 8) | (((x) & 0x0000FF00) << 8) | ((x) << 24))

void IncrementBruteGPU( unsigned char* ourBrute, unsigned int charSetLen, unsigned int brute_length, unsigned int incrementBy){
    unsigned int i = 0;
    while(incrementBy > 0 && i < brute_length){
        int add = incrementBy + ourBrute[i];
        ourBrute[i] = add % charSetLen;
        incrementBy = add / charSetLen;
        i++;
    }
    
}

uint unhex(unsigned char x)
{
    if(x <= 'F' && x >= 'A')
    {
        return  (uint)(x - 'A' + 10);
    }
    else if(x <= 'f' && x >= 'a')
    {
        return (uint)(x - 'a' + 10);
    }
    else if(x <= '9' && x >= '0')
    {
        return (uint)(x - '0');
    }
    return 0;
}

uint md5_to_ints_v0(global unsigned char* md5)
{
    uint v0 = 0;
    int i = 0;
    for(i = 0; i < 32; i+=2)
    {
        uint first = unhex(md5[i]);
        uint second = unhex(md5[i+1]);
        uint both = first * 16 + second;
        both = both << 24;
        if(i < 8)
        {
            v0 = (v0 >> 8 ) | both;
        }
    }
    
     return v0;
}

uint md5_to_ints_v1(global unsigned char* md5)
{
    uint  v1 = 0;
    int i = 0;
    for(i = 0; i < 32; i+=2)
    {
        uint first = unhex(md5[i]);
        uint second = unhex(md5[i+1]);
        uint both = first * 16 + second;
        both = both << 24;
        if (i < 16)
        {
            v1 = (v1 >> 8) | both;
        }
    }
    
    return v1;
}

uint md5_to_ints_v2(global unsigned char* md5)
{
    uint v2 = 0;
    int i = 0;
    for(i = 0; i < 32; i+=2)
    {
        uint first = unhex(md5[i]);
        uint second = unhex(md5[i+1]);
        uint both = first * 16 + second;
        both = both << 24;
        if (i < 24)
        {
            v2 = (v2 >> 8) | both;
        }

    }
    
    return v2;
}

uint md5_to_ints_v3(global unsigned char* md5)
{
    uint v3 = 0;
    int i = 0;
    for(i = 0; i < 32; i+=2)
    {
        uint first = unhex(md5[i]);
        uint second = unhex(md5[i+1]);
        uint both = first * 16 + second;
        both = both << 24;
        if(i < 32)
        {
            v3 = (v3 >> 8) | both;
        }
    }
    
    return v3;
}

//__kernel void execBrute(__global unsigned int *currentBrute, __global unsigned char *hash_buf,__global unsigned char *passwd_buf,__global uint *settings_buf){
__kernel void execBrute(__global unsigned int *currentBrute, __global unsigned char *charSet,__global uint *dest_buf, __global unsigned char *hash_buf,__global unsigned char *passwd_buf,__global uint *settings_buf){    



    unsigned char ourBrute[14]; // ourBrute[14]
    


    dest_buf[0] = md5_to_ints_v0(hash_buf);
    dest_buf[1] = md5_to_ints_v1(hash_buf);
    dest_buf[2] = md5_to_ints_v2(hash_buf);
    dest_buf[3] = md5_to_ints_v3(hash_buf);
    
    // START BRUTE AT LAST BRUTE
    for(int i = 0; i < 14; i++) // i < 14
    {
        ourBrute[i] = currentBrute[i];
    }

    //INCREMENT BRUTE
    IncrementBruteGPU(ourBrute, 63, settings_buf[0], get_global_id(0));
    
    
    for(int timer = 0; timer < 1024; timer++){

        //Now, substitute the values into the string
		char word_buf[10];

        //EMPTY WORD BUFFER
        for(unsigned int i = 0; i < settings_buf[0]; i++){
            word_buf[i] = '\0';
        }
        //FILL WORD BUFFER WITH CURRENT WORD
        for(unsigned int i = 0; i < settings_buf[0]; i++)
        {
            word_buf[i] = charSet[ourBrute[i]];
        }
        
        //CALCULCATE MD5 HASH
        md5_vfy(word_buf, settings_buf[0],dest_buf,passwd_buf);

		//INCREMENT BRUTE
        IncrementBruteGPU(ourBrute, 63, settings_buf[0], get_global_size(0));
    }
    
}



