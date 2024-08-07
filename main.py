import struct
import os

SPC_PATH = r"C:\Users\Administrator\OneDrive - mail.tust.edu.cn\桌面\py\spc\snd_pl0600_v_eng.spc"


def safeRead(data, unpackStr, expectedVal, errMsg="Not a vaild value"):
    val = struct.unpack(unpackStr, data)[0]
    if val != expectedVal:
        raise ValueError(errMsg)
    return val


def readSpcHeader(f):
    magicId = safeRead(f.read(4), "4s", b"SPAC", "Not a valid SPAC file")

    infoChunk = f.read(28)
    version, numFiles, metaCount1, metaCount2, metaOffset1, metaOffset2, dataOffset = (
        struct.unpack("IIIIIII", infoChunk)
    )
    return {
        "version": version,
        "numFiles": numFiles,
        "metaCount1": metaCount1,
        "metaCount2": metaCount2,
        "metaOffset1": metaOffset1,
        "metaOffset2": metaOffset2,
        "dataOffset": dataOffset,
    }


def readWavHeader(f):
    rawOffsets = {}
    startOffset = f.tell()
    # RIFF Chunk
    riffStr = safeRead(f.read(4), "4s", b"RIFF", "Not a valid RIFF")
    riff_chunk_size = struct.unpack("I", f.read(4))
    waveStr = safeRead(f.read(4), "4s", b"WAVE", "Not a valid WAVE")

    rawOffsets["riff"] = (startOffset, f.tell() - startOffset)
    startOffset = f.tell()

    # Format Chunk
    fmtStr = safeRead(f.read(4), "4s", b"fmt ", "Not a valid fmt ")
    fmt_chunk_size = struct.unpack("I", f.read(4))

    # Format chunk data
    (
        audio_format,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        extraParamSize,
    ) = struct.unpack("<HHIIHHH", f.read(18))
    f.seek(extraParamSize, 1)
    # audio_format:
    # Code    Description
    # 0 (0x0000)  Unknown
    # 1 (0x0001)	PCM/uncompressed
    # 2 (0x0002)	Microsoft ADPCM

    rawOffsets["fmt"] = (startOffset, f.tell() - startOffset)
    startOffset = f.tell()

    # Data Chunk (data sub-chunk)
    fmtStr = safeRead(f.read(4), "4s", b"data", "Not a valid Data chunk")
    data_chunk_size = struct.unpack("I", f.read(4))

    # <-missing dataChunk data
    rawOffsets["dataHdr"] = (startOffset, f.tell() - startOffset)
    startOffset = f.tell()

    # smpl Chunk
    smplStr = safeRead(f.read(4), "4s", b"smpl", "Not a valid fmt ")
    smpl_chunk_size = struct.unpack("I", f.read(4))
    (
        dwManufacturer,
        dwProduct,
        dwSamplePeriod,
        dwMIDIUnityNote,
        dwMIDIPitchFraction,
        dwSMPTEFormat,
        dwSMPTEOffset,
        cSampleLoops,
        cbSamplerData,
        # SampleLoop
        dwIdentifier,
        dwType,
        dwStart,
        dwEnd,
        dwFraction,
        dwPlayCount,
    ) = struct.unpack("IIIIIIIIIIIIIII", f.read(60))

    rawOffsets["smpl"] = (startOffset, f.tell() - startOffset)
    startOffset = f.tell()

    return {
        "rawOffsets": rawOffsets,
        "samplePeriod": dwSamplePeriod,
        "dataChunkSize": data_chunk_size[0],
    }


def readMeta1(f, chunkNum):
    for i in range(chunkNum):
        chunkIdx = struct.unpack("I", f.read(4))[0]
        fileNum = struct.unpack("I", f.read(4))[0]
        struct.unpack("f", f.read(4))[0]
        f.seek(4, 1)
        safeRead(f.read(4), "I", 0, "Not a valid Meta1 =0")


def readMeta2(f, chunkNum):
    for i in range(chunkNum):
        chunkIdx = struct.unpack("I", f.read(4))[0]
        trackIdx = struct.unpack("I", f.read(4))[0]
        safeRead(f.read(2), "H", 0, "Not a valid Meta2 =0")
        struct.unpack("<B", f.read(1))[0]
        struct.unpack("<B", f.read(1))[0]

        struct.unpack("IIIII", f.read(20))
        safeRead(f.read(4), "I", 100, "Not a valid Meta1 =100")
        safeRead(f.read(4), "I", 0, "Not a valid Meta1 =0")
        safeRead(f.read(4), "I", i, "Not a valid Meta1 =" + str(i))


def debug():
    f = open(
        r"C:\Users\Administrator\OneDrive - mail.tust.edu.cn\桌面\py\spc\snd_pl0600_v_eng.spc",
        "rb",
    )
    f.read(0x2D14)
    print(hex(f.tell()))
    for i in range(78):
        print(i)
        print(
            str(int(struct.unpack("<I", f.read(4))[0])),
            str(int(struct.unpack("<I", f.read(4))[0])),
            str(int(struct.unpack("<H", f.read(2))[0])),
            "\t",
            str(int(struct.unpack("<B", f.read(1))[0])),
            str(int(struct.unpack("<B", f.read(1))[0])),
        )
        struct.unpack("IIIII", f.read(20))
        str(int(struct.unpack("<I", f.read(4))[0])), str(
            int(struct.unpack("<I", f.read(4))[0])
        ), str(int(struct.unpack("<I", f.read(4))[0]))
        print()


def genWav(f, rawOffsets,datas):
    outputBaseName = os.path.splitext(SPC_PATH)[0]
    for i in range(len(rawOffsets)):
        outputPath=outputBaseName+"_"+str(i)+".wav"
        fWav=open(outputPath,'+wb')
        rawOffset = rawOffsets[i]
        f.seek(rawOffset["riff"][0])
        fWav.write(f.read(rawOffset["riff"][1]))
        f.seek(rawOffset["fmt"][0])
        fWav.write(f.read(rawOffset["fmt"][1]))
        f.seek(rawOffset["dataHdr"][0])
        fWav.write(f.read(rawOffset["dataHdr"][1]))
        fWav.write(datas[i])
        f.seek(rawOffset["smpl"][0])
        fWav.write(f.read(rawOffset["smpl"][1]))
        fWav.close()


    pass


def main():
    f = open(SPC_PATH, "rb")
    spcInfo = readSpcHeader(f)
    print(spcInfo)
    dcSize = []
    datas=[]
    rawOffsets=[]
    for i in range(spcInfo["numFiles"]):
        tmp = readWavHeader(f)
        dcSize.append(tmp["dataChunkSize"])
        rawOffsets.append(tmp["rawOffsets"])
        print(tmp)
    if f.tell() != spcInfo["metaOffset1"]:
        raise RuntimeError("mismatch metaOffset1")
    readMeta1(f, spcInfo["metaCount1"])
    if f.tell() != spcInfo["metaOffset2"]:
        raise RuntimeError("mismatch metaOffset2")
    readMeta2(f, spcInfo["metaCount2"])
    if f.tell() != spcInfo["dataOffset"]:
        raise RuntimeError("mismatch dataOffset")
    print(hex(f.tell()))
    for i in range(spcInfo["numFiles"]):
        datas.append(f.read(dcSize[i]))
    print(hex(f.tell()))

    genWav(f,rawOffsets,datas)
    f.close()


main()
# playback sample rate *=
# 0.6671430372830062

# snd_pl0600_v_eng.spc
# atk_00_00
# 1	33

# atk_01_00
# 2	50
# 3	17

# atk_03_00
# 4	45

# atk_04_00
# 5	34

# atk_04_02
# 6	35
# 7	36

# atk_05_01
# 8	37
# 9	38
# 10	39

# atk_05_03
# 11	40

# atk_06_03
# 12	46
# 13	41
# 14	42

# atk_08_00
# 15	43
# 16	44

# dmg_00_00
# 17	47

# dmg_00_01
# 18	48

# dmg_00_02
# 19	49
# 20	16

# dmg_01_00
# 21	51
# 22	52

# dmg_01_01
# 23	55

# dmg_03_00
# 24	56
# 25	57

# dmg_04_00
# 26	58
# 27	53

# dmg_08_00
# 28	54

# dmg_10_00
# 29	59
# 30	60
# 31	61

# dmg_13_00
# 32	62
# 33	63
# 34	64

# dmg_17_00
# 35	74
# 36	75

# dmg_20_00
# 37	26
# 38	27
# 39	28
# 40	29

# dmg_21_00
# 41	65
# 42	66
# 43	67

# dmg_23_00
# 44	30
# 45	31
# 46	32

# etc_00_00
# 47	72
# 48	73

# etc_02_00
# 49	68

# etc_03_01
# 50	76

# mov_01_00	16/64+193
# 51	9
# 52	10
# 53	0
# 54	1
# 55	2

# mov_01_01	192+192
# 56	3
# 57	4
# 58	5

# mov_03_00	0+192
# 59	6
# 60	7
# 61	8

# mov_04_00
# 62	13
# 63	14

# mov_06_00
# 64	19

# mov_07_01
# 65	15

# mov_08_00
# 66	18
# 67	20

# mov_10_00
# 68	21

# mov_13_00
# 69	11
# 70	12

# mov_14_00
# 71	22
# 72	23
# 73	24
# 74	25

# mov_16_00
# 75	69
# 76	70
# 77	71

# 78	77

