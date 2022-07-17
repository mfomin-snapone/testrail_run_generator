from random import random, choice, randint

class IRSequence():
    def __init__(self, pair_0, pair_1, value_to_send, num_bits, lead_in_pair=None, lead_out_pair=None):
        """
        class to store the parts of an IR sequence and format the sequence part of the pronto code from those parts.
        :type pair_0: list
        :type pair_1: list
        :type value_to_send: int
        :type num_bits: int
        :type lead_in_pair: list
        :type lead_out_pair: list
        :param pair_0: required. burst pair list that when received by the receiver represents a binary 0
        :param pair_1: required. burst pair list that when received by the receiver represents a binary 1
        :param value_to_send: required. int value to send.  Converted to binary and bits reversed so the receiver
            gets them in the right.
        :param num_bits: number of bits you want to transmit in the sequence.
        :param lead_in_pair: optional. this pair will get transmitted at the beginning of the sequence, before
            the binary pairs.
        :param lead_out_pair: optional. this pair will get transmitted at the end of the sequence, after the binary
            pairs
        """
        self.pair_0 = pair_0
        self.pair_1 = pair_1
        self.value_to_send = value_to_send
        self.num_bits = num_bits
        self.lead_in_pair = lead_in_pair
        self.lead_out_pair = lead_out_pair
        self.sequence_pronto_list = self._format_sequence()

    def _format_sequence(self):
        """
        takes the parts passed into the init of IRSequence and formats a good sequence pronto code in list format.
        :return: list of 4 digit 0 padded numeric hex strings.
        """
        sequence_pronto_list = []

        if self.lead_in_pair != None:
            sequence_pronto_list.extend(self.lead_in_pair)

        # have to reverse the bits in the value to send so the receiver gets it in the right order
        if self.value_to_send >= self.max_bit_number(self.num_bits):
            raise ValueError('value_to_send is: {0}, num_bits is: {1}.  The highest {1} bit number that can be '
                             'sent is {2}.  Pass a number below that in value_to_send.'
                             .format(self.value_to_send, self.num_bits, self.max_bit_number(self.num_bits)))
        send_this = self.reverseBits(self.value_to_send, self.num_bits)
        # print(send_this)
        for bit in send_this:
            if bit == '0':
                sequence_pronto_list.extend(self.pair_0)
            if bit == '1':
                sequence_pronto_list.extend(self.pair_1)

        if self.lead_out_pair != None:
            sequence_pronto_list.extend(self.lead_out_pair)

        return sequence_pronto_list

    def reverseBits(self, num, bitSize):
        """
        takes an integer number in num, converts it to binary, reverses it, then pads it with 0's depending on how
            many bits.
        :param num: required. integer number you want converted to binary and reversed
        :param bitSize: desired bit width of the returned binary reversed number.
        :return: string of the reversed binary number with the proper number of 0's padded based on bit width.
        """
        # convert number into binary representation.  Output will be like bin(10) = '0b10101'
        binary = bin(num)
        # print(binary)

        # skip first two characters of binary representation string and reverse remaining string and then
        # append zeros after it. binary[-1:1:-1]  --> start from last character and reverse it until
        # second last character from left
        reverse = binary[-1:1:-1]
        reverse = reverse + (bitSize - len(reverse)) * '0'

        return reverse

    def max_bit_number(self, num_bits):
        bin_str = '1' * num_bits
        max_num = int(bin_str, 2)
        return max_num


class IRUtilities():
    def __init__(self):
        pass

    def generate_random_pronto(self, min_frequency, max_frequency, min_bits=8, max_bits=32, min_pair_val=10
                               , max_pair_val=65535, toString=True):
        """
        Generates a random pronto code.  use the min max values for frequency, bits and pair values to fine tune the
            range of values possible in the pronto code.
        :type min_frequency: int or str
        :type max_frequency: int or str
        :type min_bits: int
        :type max_bits: int
        :type min_pair_val: int or str
        :type max_pair_val: int or str
        :type toString: bool
        :param min_frequency: required. minimum value for either int frequency in hz or 4 digit 0 padded numeric
            hex string ready to be inserted into the pronto code frequency segment.
        :param max_frequency: required. maximum value for either int frequency in hz or 4 digit 0 padded numeric
            hex string ready to be inserted into the pronto code frequency segment.
        :param min_bits: integer minimum number of burst pairs to be transmitted per sequence.  for example, if 8
            then the minimum number of burst pairs per sequence is 8 burst pairs.
        :param max_bits: integer maximum number of burst pairs to be transmitted per sequence.  for example, if 32
            then the maximum number of burst pairs per sequence is 32 burst pairs.
        :param min_pair_val: minimum value for burst pair segment.  accepts either a base 10 integer value or 4 digit 0
            padded numeric hex string.  For example 40 or '0028'.  This means the random generated burst pair segments
            will have a minimum value of 40 or hex 28.  This is used for pair_0, pair_1, lead in and lead out burst
            pairs
        :param max_pair_val: maximum value for burst pair segment.  accepts either a base 10 integer value or 4 digit 0
            padded numeric hex string.  For example 507 or '01fb'.  This means the random generated burst pair segments
            will have a maximum value of 507 or hex 1fb.  This is used for pair_0, pair_1, lead in and lead out burst
            pairs.  max value is ffff or 65535
        :param toString: bool.  True if you want a string pronto code returned.  False if you want the list of pronto
            values
        :return: Either the string pronto code ro list of pronto values depending on the value of toString
        """
        sequence_1 = None
        sequence_2 = None
        pronto_list = ['0000']

        # handle frequency and add to pronto
        min_frequency_type = type(min_frequency)
        max_frequency_type = type(max_frequency)

        if min_frequency_type == int and max_frequency_type == int:
            if min_frequency < 64 or max_frequency < 64:
                raise ValueError('The value for min and max frequency has to be > 63 otherwise the resulting encoded '
                                 'value for frequency is > ffff.  I got min_frequency: {0}.  max_frequency: {1}'
                                 .format(min_frequency, max_frequency))
            if min_frequency > max_frequency:
                raise ValueError('min_frequency value of: {0}, cant be greater than max_frequency value of: {1}.  '
                                 'fix it and try again'.format(min_frequency, max_frequency))
            freq = randint(min_frequency, max_frequency)
            pronto_list.append('{0:04x}'.format(int(round(4145146.0 / freq))))
        elif min_frequency_type == str and max_frequency_type == str:
            if len(min_frequency) != 4 or len(min_frequency) != 4:
                raise ValueError('string length of frequency has to be 4.  This arg only supports 0 padded 4 digit '
                                 'hex strings.  min_frequency: {0} which has a length of {1}.  max_frequency: {2} '
                                 'which has a length of {3}'.format(min_frequency, len(min_frequency), max_frequency
                                                                    , len(max_frequency)))
            min_frequency_int = int(min_frequency, 16)
            max_frequency_int = int(max_frequency, 16)
            if min_frequency_int < 64 or max_frequency_int < 64:
                # Im using the int conversion here to make sure the string is valid hex.  If it isn't, the
                # conversion raises a value error exception.  No else is necessary cause we've handled all possibilities.
                raise ValueError('The value for min and max frequency has to be > 63 otherwise the resulting encoded '
                                 'value for frequency is > ffff.  I got min_frequency: {0}.  max_frequency: {1}'
                                 .format(min_frequency, max_frequency))
            if min_frequency_int > max_frequency_int:
                raise ValueError('min_frequency_int value of: {0}, cant be greater than max_frequency_int: {1}.  '
                                 'try again'.format(min_frequency_int, max_frequency_int))
            freq = randint(min_frequency_int, max_frequency_int)
            pronto_list.append('{0:04x}'.format(int(round(4145146.0 / freq))))
        else:
            raise ValueError('the frequency arg supports types str or int.  I got min_frequency: {0} which is '
                             'type: {1}.  max_frequency: {2}, which is type: {3}.  Fix and try again'
                             .format(min_frequency, type(min_frequency), max_frequency, type(max_frequency)))

        # generate random sequence(s).
        num_sequences = randint(1, 3)  # 1 = 01 or seq 1 blank seq 2 populated, 2 = 10 or seq 1 populated and seq 2
        # blank, 3 = 11 or both seq 1 and seq 2 populated.
        if num_sequences == 1:
            sequence_1 = self.generate_random_sequence(min_bits, max_bits, min_pair_val, max_pair_val)
        elif num_sequences == 2:
            sequence_2 = self.generate_random_sequence(min_bits, max_bits, min_pair_val, max_pair_val)
        elif num_sequences == 3:
            sequence_1 = self.generate_random_sequence(min_bits, max_bits, min_pair_val, max_pair_val)
            sequence_2 = self.generate_random_sequence(min_bits, max_bits, min_pair_val, max_pair_val)

        # add sequence lengths to the pronto.
        seq1_length = 0
        seq2_length = 0
        if isinstance(sequence_1, IRSequence):
            seq1_length = len(sequence_1.sequence_pronto_list)
        if isinstance(sequence_2, IRSequence):
            seq2_length = len(sequence_2.sequence_pronto_list)

        pronto_list.append('{0:04x}'.format(seq1_length))
        pronto_list.append('{0:04x}'.format(seq2_length))

        # add sequence(s) to the pronto
        if isinstance(sequence_1, IRSequence):
            pronto_list.extend(sequence_1.sequence_pronto_list)
        if isinstance(sequence_2, IRSequence):
            pronto_list.extend(sequence_2.sequence_pronto_list)

        if toString:
            return ' '.join(pronto_list)
        else:
            return pronto_list

    def generate_random_sequence(self, min_bits, max_bits, min_pair_val, max_pair_val):
        lead_in_pair = None
        lead_out_pair = None
        min_pair_type = type(min_pair_val)
        max_pair_type = type(max_pair_val)
        if min_bits > max_bits:
            raise ValueError('min_bits value of: {0} is > max_bits value of: {1}.  min_bits has to be <= max_bits'
                             .format(min_bits, max_bits))
        min_bit_num = self.max_bit_number(min_bits)

        if min_pair_type and max_pair_type == int:
            pass
        elif min_pair_type and max_pair_type == str:
            if len(min_pair_val) != 4 or len(max_pair_val) != 4:
                raise ValueError('min_pair_val or max_pair_val are strings of a length other than 4.  If its passed '
                                 'in as a string this only supports 4 digit 0 padded hex strings.  i got '
                                 'min_pair_val: {0}, length: {1}.  max_pair_val: {2}, length: {3}'
                                 .format(min_pair_val, len(min_pair_val), max_pair_val, len(max_pair_val)))
            # min_pair and max_pair are hex strings like 00fb, convert it to int which also checks to make sure
            # its a valid numeric hex string.
            min_pair_val = int(min_pair_val, 16)
            max_pair_val = int(max_pair_val, 16)
        else:
            raise TypeError('min_pair_val is type: {0}, max_pair_val is" {1}.  This method supports only type int '
                            'or str.  Both min and max pair values need to be the same type'
                            .format(min_pair_type, max_pair_type))

        # generate random burst pairs to use in the sequence
        pair_0 = self.generate_burst_pair(min_pair_val, max_pair_val)
        pair_1 = self.generate_burst_pair(min_pair_val, max_pair_val)

        num_bits = randint(min_bits, max_bits)

        value_to_send = randint(1, self.max_bit_number(num_bits))

        use_lead_in = randint(0, 1)
        use_lead_out = randint(0, 1)
        if use_lead_in:
            lead_in_pair = self.generate_burst_pair(min_pair_val, max_pair_val)
        if use_lead_out:
            lead_out_pair = self.generate_burst_pair(min_pair_val, max_pair_val)

        sequence = IRSequence(pair_0, pair_1, value_to_send, num_bits, lead_in_pair, lead_out_pair)
        return sequence

    def generate_burst_pair(self, min_pair_int, max_pair_int):
        """
        Generates a random burst pair whose on/off durations are a random value between min_pair_int and max_pair_int
        :type min_pair_int: int
        :type max_pair_int: int
        :param min_pair_int: required. minimum int pair value
        :param max_pair_int: required. maximum int pair value
        :return:
        """
        burst1_int = randint(min_pair_int, max_pair_int)
        burst2_int = randint(min_pair_int, max_pair_int)
        burst1_str = '{0:04x}'.format(burst1_int)
        burst2_str = '{0:04x}'.format(burst2_int)
        return [burst1_str, burst2_str]

    def generate_pronto(self, frequency, sequence1_class=None, sequence2_class=None, toString=True):
        """
        generates a pronto code with a given frequency and IRSequence class(es).
        :type frequency: int or str
        :type sequence1_class: IRSequence
        :type sequence2_class: IRSequence
        :type toString: bool
        :param frequency: required. int frequency in hz or 4 digit 0 padded numeric hex string.  The hex string is
            the same thing that shows up in the frequency part of a pronto code
        :param sequence1_class: instantiated IRSequence class.  One or both need to be passed in
        :param sequence2_class: instantiated IRSequence class.  One or both need to be passed in
        :param toString: bool.  True if you want a string pronto code returned.  False if you want a pronto in list format
        :return: string or list pronto code based off the value of toString
        """

        if sequence1_class == None and sequence2_class == None:
            raise ValueError('sequence1_class and sequence2_class cant both be None.  Pass in a properly '
                             'instantiated IRSequence class for 1 or both of them.  For the first i got: {0}.  '
                             'For the second i got: {1}'.format(sequence1_class, sequence2_class))

        pronto_list = ['0000']

        # handle frequency and add to pronto
        if isinstance(frequency, int):
            if frequency < 64:
                raise ValueError('The value for frequency has to be > 63 otherwise the resulting encoded value for '
                                 'frequency is > ffff.  I got {0}'.format(frequency))
            pronto_list.append('{0:04x}'.format(int(round(4145146.0 / frequency))))
        elif isinstance(frequency, str):
            if len(frequency) != 4:
                raise ValueError('string length of frequency has to be 4.  This arg only supports 0 padded 4 digit '
                                 'hex strings.  I got: {0} which has a length of {1}'
                                 .format(frequency, len(frequency)))
            elif int(frequency, 16) > 0:
                # Im using the int conversion here to make sure the string is valid hex.  If it isn't, the
                # conversion raises a value error exception.  No else is necessary cause we've handled all possibilities.
                pronto_list.append(frequency)
        else:
            raise ValueError('the frequency arg supports types str or int.  I got value: {0} which is type: {1}.  '
                             'fix and try again'.format(frequency, type(frequency)))

        # add sequence lengths to the pronto.
        seq1_length = 0
        seq2_length = 0
        if isinstance(sequence1_class, IRSequence):
            seq1_length = len(sequence1_class.sequence_pronto_list)
        if isinstance(sequence2_class, IRSequence):
            seq2_length = len(sequence2_class.sequence_pronto_list)

        pronto_list.append('{0:04x}'.format(seq1_length))
        pronto_list.append('{0:04x}'.format(seq2_length))

        # add sequence(s) to the pronto
        if isinstance(sequence1_class, IRSequence):
            pronto_list.extend(sequence1_class.sequence_pronto_list)
        if isinstance(sequence2_class, IRSequence):
            pronto_list.extend(sequence2_class.sequence_pronto_list)

        if toString:
            return ' '.join(pronto_list)
        else:
            return pronto_list

    def max_bit_number(self, num_bits):
        """
        returns the largest possible integer for the number of bits passed in.  for example: the largest 9 bit number
            is 111111111 in binary.  Thats 511.  so this returns 511 if you pass in 9 as num_bits
        :type num_bits: int
        :param num_bits: number of bits
        :return: int with the largest number possible given the passed in number of bits
        """
        bin_str = '1' * num_bits
        max_num = int(bin_str, 2)
        return max_num

if __name__ == '__main__':
    ir = IRUtilities()
    # for x in range(10):
    #     code = ir._temp_create_pronto(70000, 5, 6)
    #     print(code)

    # ir.create_pronto2('001f', seq1_pair=['0015', '0030'], seq1_length=20)
    # ir.create_pronto(48000, seq1_pair=['0015', '0030'], seq1_length=20)

    # seq1 = IRSequence(['0015', '0030'], ['0045', '0090'], 10, 8, lead_in_pair=['0025', '0035'])
    # seq2 = IRSequence(['0080', '0160'], ['0090', '0180'], 5000, 12, lead_in_pair=['0050', '0100'])
    # print(seq1.sequence_pronto_list)

    # print(ir.generate_pronto(48000, seq1, seq2))
    # print(ir.generate_pronto(48000
    #                          # , sequence1_class=seq1
    #                          , sequensequence_2ce2_class=seq2
    #                          ))

    # pronto = ir.generate_random_pronto('0056', '01ff', max_bits=64)
    for x in range(100):
        pronto = ir.generate_random_pronto(38000, 60000, max_bits=32, max_pair_val=1000)
        print(pronto)
