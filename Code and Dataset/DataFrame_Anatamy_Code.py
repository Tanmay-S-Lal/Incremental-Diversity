
import time
import math
from tabulate import tabulate
import copy
import matplotlib.pyplot as plt
import pandas as pd


def displayTable2(table, title=None, sensitive=False, sensitive_attribute=None):
    """ Better function to display the data in tables using tabulate library """

    all_data = []

    if sensitive:   # Only ST Count Table

        sensitive_count_dict = copy.deepcopy(table)

        print("\n\t\t\tDISPLAYING {} COUNT\n".format(sensitive_attribute))

        for group_id, current_eq_class in sensitive_count_dict.items():

            for sensitive_value, sensitive_count in current_eq_class.items():

                values = [group_id, sensitive_value, sensitive_count]

                all_data.append(values)

        print(tabulate(all_data, headers=[
              "Group ID", sensitive_attribute, "Count"]))

    else:   # Other Tables

        print("\n\t\t\tDISPLAYING {}\n".format(title))

        all_data = [record.values() for record in table.values()]

        headings = None
        for no in table:    # Running loop only once because we need attribute names only
            headings = table[no].keys()
            break

        print(tabulate(all_data, headers=headings))

    print("______________________________________________________")

    return


def getNoOfUniqueValues(table, sensitive_attribute):
    """ Returns the no. of unique values of Sensitive Attribute present in the table """

    lst = []
    for record in table.values():

        value = record[sensitive_attribute]
        if value not in lst:
            lst.append(value)

    return len(lst)


def getMicrodata(no_of_records, K, sensitive_attribute, display):
    """ Returns the Microdata & Extra Time taken for displaying the microdata table. """

    final_lines = None

    with open("datasetEL.txt", 'r') as file:
        final_lines = file.readlines()[1:no_of_records+1]

    diction = {}

    for i, line in enumerate(final_lines):

        slno = i+1

        diction[slno] = {}

        attributes = line.split(',')
        diction[slno]["Age"] = attributes[0].strip()
        diction[slno]["Gender"] = attributes[1].strip()
        diction[slno]["Zip Code"] = attributes[2].strip()
        diction[slno]["Education"] = attributes[3].strip()
        diction[slno]["Employment"] = attributes[4].strip()
        diction[slno]["Marital Status"] = attributes[5].strip()
        diction[slno]["Marital Parent"] = getParent(
            diction[slno]["Marital Status"])
        diction[slno]["Relationship"] = attributes[6].strip()
        diction[slno]["Race"] = attributes[7].strip()
        diction[slno]["Salary"] = attributes[8].strip()
        diction[slno]["Disease"] = attributes[9].replace("\n", "").strip()
        diction[slno]["Disease Parent"] = getDiseaseParent(
            diction[slno]["Disease"])

        diction[slno]["Group ID"] = ((slno-1)//K)+1
        # OR
        #diction[slno]["Group ID"] = math.floor((slno-1)/K) + 1

    # Displaying Microdata Table here because it is giving shuffled Group ID for some records outside this function
    extra = 0
    if display:
        t1 = time.time()
        displayTable2(diction, "MICRODATA")
        t2 = time.time()
        extra = t2-t1

    return diction, extra


def getValuesInEq(diction, attribute_name):

    return [record[attribute_name] for record in diction.values()]


def getParent(child):

    tree = {"Married": ["Married-civ-spouse", "Married-spouse-absent", "Married-AF-spouse"],
            "Unmarried": ["Never-married", "Divorced", "Separated", "Widowed"]
            }

    for parent, children in tree.items():

        if child in children:
            return parent

    else:

        raise Exception("PARENT NOT FOUND")


def ParentsCheck(value, existing_values, algo):
    """ Checks if a record can be added in EQ class (True) or Not (False) """

    parent = getParent(value)

    existing_parents = list(map(getParent, existing_values))

    if algo == 2 or algo == -100:

        return parent not in existing_parents

    elif algo == 3:

        # After adding in EQ Class, becomes two common parents in EQ
        return existing_parents.count(parent) <= 1

    else:
        raise Exception("ParentCheck function error")


def getDiseaseParent(child):

    tree = {"Respiratory disease": ["Asthama", "Pneumonia", "Emphysema"],
            "Excretory_system disorder": ["Uremia", "Nephritis", "Oedema"],
            "Circulatory_system disorder": ["Cardiac arrest", "Angina Pectoris", "Cardiomyopathy"],
            "Digestive disorder": ["Gastritis", "Jaundice", "Diarrhoea"],
            "Mental disorder": ["Insomnia", "Schizophernia", "Dementia"]}

    for parent, children in tree.items():

        if child in children:
            return parent

    raise Exception("PARENT NOT FOUND for {}".format(child))


def DiseaseParentsCheck(value, existing_values):
    """ Checks if a record can be added in EQ class (True) or Not (False) """

    parent = getDiseaseParent(value)

    existing_parents = list(map(getDiseaseParent, existing_values))

    return parent not in existing_parents


def diversifyRecords(table, no_of_records, K, algo, sensitive_attribute):
    """ This function rearranges the records based on Marital Status and
    returns the New Microdata Dictionary. """

    """ 1) We create a separate dictionary to store values that do not fit in the current dictionary .
        and then later add the separated values back into the dictionary. """

    original_table = copy.deepcopy(table)

    temp_dict = {}
    new_dict = {}

    # Creating new_dict nested structure
    max_group_id = math.ceil(no_of_records/K)

    # Creating Group IDs
    for i in range(1, max_group_id+1):

        new_dict[i] = {}      # Stores as {1:{}, 2:{}}

    for record_no, record in original_table.items():    # Each Record

        sensitive_value = record[sensitive_attribute]
        group_id = record["Group ID"]

        # Selecting the EQ Class corresponding to the Record's Group ID
        current_eq_class = new_dict[group_id]

        # Getting all Marital Status in that Equivalence Class
        existing_sensitive_values = getValuesInEq(
            current_eq_class, sensitive_attribute)

        # Adding in temp or new dict
        check = None
        if algo in [1, 4]:
            check = sensitive_value not in existing_sensitive_values

        elif algo in [2, 3, -100]:
            check = ParentsCheck(
                sensitive_value, existing_sensitive_values, algo)

        elif algo == 5:
            check = DiseaseParentsCheck(
                sensitive_value, existing_sensitive_values)

        if check:  # Sensitive Value can be added in EQ class

            current_eq_class[record_no] = record    # Storing value in new_dict

        else:   # Sensitive Value cannot be added in EQ class

            record["Group ID"] = "NA"
            # Storing value in temp_dict
            temp_dict[record_no] = record

    """ 2) We have to pick and place values from temp_dict into new_dict to see where it fits. """

    # To store records that do not fit in any eq class
    residue_dict = copy.deepcopy(temp_dict)

    for temp_record_no, temp_record in temp_dict.items():     # Each record in temp_dict

        temp_sensitive_value = temp_record[sensitive_attribute]

        for eq_no, current_eq_class in new_dict.items():      # Each Equivalence Class

            existing_sensitive_values = getValuesInEq(
                current_eq_class, sensitive_attribute)

            # Conditions for records from temp_dict to be added into Modified Microdata Table

            check1 = None
            if algo in [1, 4]:
                # Unique Marital Status value in a EQ Class
                check1 = temp_sensitive_value not in existing_sensitive_values

            elif algo in [2, 3, -100]:
                check1 = ParentsCheck(
                    temp_sensitive_value, existing_sensitive_values, algo)

            elif algo == 5:
                check1 = DiseaseParentsCheck(
                    temp_sensitive_value, existing_sensitive_values)

            # No. fo records in EQ Class is < K
            check2 = len(current_eq_class) < K

            if check1 and check2:

                # Updating Group ID of the record to Equivalence Class No.
                temp_record["Group ID"] = eq_no

                # Adding record from temp_dict to eq_class where it fits
                current_eq_class[temp_record_no] = temp_record

                # Deleting record from Residue after giving it to New Dictionary
                del residue_dict[temp_record_no]

                # Exiting inner loop and going for next record
                break

    # No additional diversification for algo = -100
    if algo == -100:

        latest_dict = {}

        for eq_no, current_eq_class in new_dict.items():  # Each Equivalence Class

            for record_no, record in current_eq_class.items():  # Each Record

                # Adding records in latest_dict
                latest_dict[record_no] = record

        """ 7) Returning the Modified Microdata Table and the Residue Dictionary """

        return latest_dict, residue_dict

    """ Secondary Sensitive Attribute """

    """ 3) Exchanging Education values > 1 """

    for eq_no in new_dict.copy():  # Each Equivalence Class

        current_eq_class = new_dict[eq_no]

        for record_no in current_eq_class.copy():  # Each Record

            record = current_eq_class[record_no]

            if getValuesInEq(current_eq_class, "Education").count(record["Education"]) > 1:

                # Finding Record in residue_dict with similar Sensitive Value
                for residue_no in residue_dict.copy():

                    residue_record = residue_dict[residue_no]

                    check1 = None
                    if algo in [1, 4]:
                        # Not disturbing Primary Sensitive Attribute
                        check1 = residue_record[sensitive_attribute] == record[sensitive_attribute]

                    elif algo in [2, 3]:
                        parent1 = getParent(
                            residue_record[sensitive_attribute])
                        parent2 = getParent(record[sensitive_attribute])

                        check1 = parent1 == parent2    # Not disturbing the Parent values

                    elif algo == 5:
                        parent1 = getDiseaseParent(
                            residue_record[sensitive_attribute])
                        parent2 = getDiseaseParent(record[sensitive_attribute])

                        check1 = parent1 == parent2    # Not disturbing the Parent values

                    check2 = residue_record["Education"] != record["Education"]

                    if check1 and check2:

                        # Exchanging record

                        residue_record["Group ID"] = eq_no

                        new_dict[eq_no][residue_no] = copy.deepcopy(
                            residue_record)  # Adding in modified dictionary
                        residue_dict[record_no] = copy.deepcopy(record)

                        del new_dict[eq_no][record_no]
                        del residue_dict[residue_no]

                        break   # We have performed the exchange operation

                    else:
                        continue

            else:
                continue

    """ Tertiary Sensitive Attribute """

    """ 4) Exchanging Employment values > 1 """

    for eq_no in new_dict.copy():  # Each Equivalence Class

        current_eq_class = new_dict[eq_no]

        for record_no in current_eq_class.copy():  # Each Record

            record = current_eq_class[record_no]

            if getValuesInEq(current_eq_class, "Employment").count(record["Employment"]) > 1:

                # Finding Record in residue_dict with similar Sensitive Value
                for residue_no in residue_dict.copy():

                    residue_record = residue_dict[residue_no]

                    check1 = None
                    if algo in [1, 4]:
                        # Not disturbing Primary Sensitive Attribute
                        check1 = residue_record[sensitive_attribute] == record[sensitive_attribute]

                    elif algo in [2, 3]:
                        parent1 = getParent(
                            residue_record[sensitive_attribute])
                        parent2 = getParent(record[sensitive_attribute])

                        check1 = parent1 == parent2    # Not disturbing the Parent values

                    elif algo == 5:
                        parent1 = getDiseaseParent(
                            residue_record[sensitive_attribute])
                        parent2 = getDiseaseParent(record[sensitive_attribute])

                        check1 = parent1 == parent2    # Not disturbing the Parent values

                    # Not disturbing Secondary SA
                    check2 = residue_record["Education"] == record["Education"]

                    check3 = residue_record["Employment"] != record["Employment"]

                    if check1 and check2 and check3:

                        # Exchanging record

                        residue_record["Group ID"] = eq_no

                        new_dict[eq_no][residue_no] = copy.deepcopy(
                            residue_record)  # Adding in modified dictionary
                        residue_dict[record_no] = copy.deepcopy(record)

                        del new_dict[eq_no][record_no]
                        del residue_dict[residue_no]

                        break   # We have performed the exchange operation

                    else:
                        continue

            else:
                continue

    """ Quaternary Sensitive Attribute """

    """ 5) Exchanging Race values > 1 """

    for eq_no in new_dict.copy():  # Each Equivalence Class

        current_eq_class = new_dict[eq_no]

        for record_no in current_eq_class.copy():  # Each Record

            record = current_eq_class[record_no]

            if getValuesInEq(current_eq_class, "Race").count(record["Race"]) > 1:

                # Finding Record in residue_dict with similar Sensitive Value
                for residue_no in residue_dict.copy():

                    residue_record = residue_dict[residue_no]

                    check1 = None
                    if algo in [1, 4]:
                        # Not disturbing Primary Sensitive Attribute
                        check1 = residue_record[sensitive_attribute] == record[sensitive_attribute]

                    elif algo in [2, 3]:
                        parent1 = getParent(
                            residue_record[sensitive_attribute])
                        parent2 = getParent(record[sensitive_attribute])

                        check1 = parent1 == parent2    # Not disturbing the Parent values

                    elif algo == 5:
                        parent1 = getDiseaseParent(
                            residue_record[sensitive_attribute])
                        parent2 = getDiseaseParent(record[sensitive_attribute])

                        check1 = parent1 == parent2    # Not disturbing the Parent values

                    # Not disturbing Secondary SA
                    check2 = residue_record["Education"] == record["Education"]

                    # Not disturbing Tertiary SA
                    check3 = residue_record["Employment"] == record["Employment"]

                    check4 = residue_record["Race"] != record["Race"]

                    if check1 and check2 and check3 and check4:

                        # Exchanging record

                        residue_record["Group ID"] = eq_no

                        new_dict[eq_no][residue_no] = copy.deepcopy(
                            residue_record)  # Adding in modified dictionary
                        residue_dict[record_no] = copy.deepcopy(record)

                        del new_dict[eq_no][record_no]
                        del residue_dict[residue_no]

                        break   # We have performed the exchange operation

                    else:
                        continue

            else:
                continue

    """ 6) Converting the format of New Dictionary to the same as that of Original Dictionary """

    latest_dict = {}

    for eq_no, current_eq_class in new_dict.items():  # Each Equivalence Class

        for record_no, record in current_eq_class.items():  # Each Record

            latest_dict[record_no] = record     # Adding records in latest_dict

    """ 7) Returning the Modified Microdata Table and the Residue Dictionary """

    return latest_dict, residue_dict


def getTwoTables(diction, sensitive_attribute):
    """ Segregates the Microdata Table into QIT and ST """

    qit_table = {}
    st_table = {}

    for no, record in diction.items():  # Each Record

        qit_table[no] = {}  # Each Record in QIT
        st_table[no] = {}   # Each Record in ST

        for attribute_name, value in record.items():   # Each Attribute

            if attribute_name == sensitive_attribute:  # Storing in Sensitive Table

                st_table[no][attribute_name] = value

            else:   # Storing in QIT Table

                qit_table[no][attribute_name] = value

        # Storing Group ID
        qit_table[no]["Group ID"] = record["Group ID"]
        st_table[no]["Group ID"] = record["Group ID"]

    return qit_table, st_table


def getSensitiveCount(st_table, no_of_records, K, sensitive_attribute):
    """ Returns a dictionary as {1:{"pneumonia":2, "flu":2}, 2:{...}} where 1,2 are Group IDs """

    """ OR {"pneumonia":{"Count":2,"Group ID":1}, "flu":{...}} """  # This won't work for disease present in different Group IDs

    """ We have chosen the former approach """

    sensitive_count_dict = {}

    max_group_id = math.ceil(no_of_records/K)

    # Creating Group IDs nested structure
    for i in range(1, max_group_id+1):

        sensitive_count_dict[i] = {}      # Stores as {1:{}, 2:{}}

    for record_no, record in st_table.items():  # Each Record

        group_id = record["Group ID"]
        sensitive_value = record[sensitive_attribute]

        # Particular Equivalence Class corresponding to record's Group ID
        current_eq_class = sensitive_count_dict[group_id]

        # Checking if Sensitive Attribute already exists in the eq class
        if sensitive_value in current_eq_class.keys():

            current_eq_class[sensitive_value] += 1

        else:   # Creating "sensitive_attribute":<count> pair

            current_eq_class[sensitive_value] = 1

    return sensitive_count_dict


def maskData(attribute_name, value, group_id):

    if attribute_name == "Age":

        """ Based on Group ID.
            Three Ranges: 1:10, 2:20, 3:30 """

        age = int(value)

        factor = (group_id-1) % 3 + 1

        lower = age - age % 10
        upper = lower + 10*factor - 1

        return "({} - {})".format(lower, upper)

    elif attribute_name == "Gender":

        return "M/F"

    elif attribute_name == "Zip Code":

        zip_code = str(value)

        return zip_code[:-3] + "*"*3

    elif attribute_name == "Employment":

        return "*"

    elif attribute_name == "Race":

        return "*"

    elif attribute_name == "Salary":

        return "*"

    else:

        return "NOT YET DEFINED"


def getMaskedDictionary(microdata, attributes_to_mask):
    """ Returns the Masked Dictionary """

    mask_dict = copy.deepcopy(microdata)

    for record in mask_dict.values():  # Each Record

        for attribute_name in attributes_to_mask:   # Each Attribute to Mask

            # Updating with masked value
            record[attribute_name] = maskData(
                attribute_name, record[attribute_name], record["Group ID"])

    return mask_dict


def getTimePerformance(start, end, extra):
    """ Returns the Total Time taken in ms rounded to 4 places of decimal """

    return round((end - start - extra) * 1000, 4)


def getResiduePercentage(no_of_records, diction):
    """ Returns the Residue % rounded to 2 places of decimal """

    return round(len(diction)/no_of_records * 100, 2)


def getDiversityPerc(received_table, no_of_records, K, verbose=False):
    """ Returns the Diverstiy of the Modified Microdata Table rounded to 2 places of decimal """

    table = copy.deepcopy(received_table)

    grand_div = None    # Final Average of Table
    eq_divs = []        # Average of Each EQ

    # Diversity is calculated for these non-masked attributes
    attributes_diversity = ["Education", "Employment", "Marital Status", "Marital Parent",
                            "Relationship", "Race", "Salary", "Disease", "Disease Parent"]

    # Creating eq_dict nested structure
    eq_dict = {}

    max_group_id = math.ceil(no_of_records/K)

    # Creating Group IDs
    for i in range(1, max_group_id+1):

        eq_dict[i] = {}      # Stores as {1:{}, 2:{}}

    # Assigning Record to its Respective EQ Class
    for record_no, record in table.items():

        eq_dict[record["Group ID"]][record_no] = record

    # Calculating Diversity
    for eq_no, current_eq_class in eq_dict.items():    # Each EQ Class

        current_eq_avg = 0

        for attribute_name in attributes_diversity:     # Each Attribute

            values = getValuesInEq(current_eq_class, attribute_name)

            # Unique Values / Total Values
            div = round(len(set(values))/len(values), 2)

            current_eq_avg += div

            if verbose:
                print("\nDiversity for {} in EQ {} = {}\n".format(
                    attribute_name, eq_no, div))

        current_eq_avg = round(current_eq_avg/len(attributes_diversity), 2)

        eq_divs.append(current_eq_avg)

        if verbose:
            print("\nDiversity for EQ {} = {}\n".format(eq_no, current_eq_avg))

    grand_div = sum(eq_divs)/max_group_id

    return round(grand_div*100, 2)


def displayPerformance(no_of_records, unique, K, sensitive_attribute,
                       total_time, residue_percentage, diversity_percentage,
                       algo):

    algo_names = {1: "Marital Status Unique",
                  2: "Semantic Tree (One Parent)",
                  3: "Semantic Tree (Two Parents)",
                  4: "Relationship Unique",
                  5: "Disease Semantic Tree",
                  -100: "Paper Algo"}

    total_time = "{:.4f} ms".format(total_time)
    residue_percentage = "{:.2f} %".format(residue_percentage)
    diversity_percentage = "{:.2f} %".format(diversity_percentage)

    print("\n\t\t\tDISPLAYING PERFORMANCE PARAMETERS (Records = {}, k = {}, Algo = {}) \n".format(no_of_records,
                                                                                                  K,
                                                                                                  algo_names[algo]))

    # 2D List because tabulate works with 2D lists
    all_data = [[unique, total_time, residue_percentage, diversity_percentage]]

    headings = ["No. of Unique Values for {}".format(sensitive_attribute),
                "Code Runtime",
                "Residue Records %",
                "Diversity %"]

    print(tabulate(all_data, headers=headings))

    print("______________________________________________________")

    return


def NestedDictionaryToDataFrame(masked_microdata):

    diction = copy.deepcopy(masked_microdata)

    # Initialising Columns
    columns = None
    for no in diction:    # Running loop only once because we need attribute names only
        columns = diction[no].keys()
        break

    # Initialising Final Data List
    data_list = [record.values() for record in diction.values()]

    df = pd.DataFrame(data_list, columns=columns)

    return df, columns


def displayDF(df, headers):
    print("\nDISPLAYING DATAFRAME\n")
    print(tabulate(df, headers=headers))


def main(no_of_records, K, algo, display=False):
    """ 
        Spearheads the beginning of the Algorithm and returns the Performance Parameters.

        Five Algorithms can be chosen:
        1) Marital Status present only once
        2) Marital Status Semantic Tree only One Count
        3) Marital Status Semantic Tree with Two Count
        4) Relationship present only once
        5) Disease Semantic Tree

        -100) Paper Algo (l,e diversity) (like 2nd algo)

    """

    # Starting Time
    start = time.time()

    extra = 0   # For extra wastage time

    # Determining Sensitive Attribute according to Algorithm chosen
    sensitive_attribute = "Marital Status"  # For algo 1,2,3, -100

    if algo == 4:
        sensitive_attribute = "Relationship"
    elif algo == 5:
        sensitive_attribute = "Disease"

    # 1) Getting Microdata, QIT & ST Tables

    original_table, extra = getMicrodata(
        no_of_records, K, sensitive_attribute, display)

    # 2) Diversify Records

    new_original_table = None
    residue_dict = None

    new_original_table, residue_dict = diversifyRecords(
        original_table, no_of_records, K, algo, sensitive_attribute)

    no_of_unique_values_for_senstive_attribute = getNoOfUniqueValues(
        original_table, sensitive_attribute)

    # 3) Getting QIT and ST Tables

    qit_table, st_table = getTwoTables(new_original_table, sensitive_attribute)
    sensitive_count_dict = getSensitiveCount(
        st_table, no_of_records, K, sensitive_attribute)

    # 4) Masking

    attributes_to_mask = ["Gender", "Age", "Zip Code"]

    masked_microdata = getMaskedDictionary(
        new_original_table, attributes_to_mask)

    # End Time for Program Run
    end = time.time()

    # 5) Displaying All Tables

    if (display):

        # Original Microdata is displayed in get getMicrodata() function itself

        displayTable2(table=new_original_table, title="MODIFIED MICRODATA")

        displayTable2(qit_table, title="QIT")

        displayTable2(st_table, title="ST")     # Without Marital Count

        displayTable2(sensitive_count_dict, title=None,
                      sensitive=True, sensitive_attribute=sensitive_attribute)

        displayTable2(masked_microdata, title="MASKED MICRODATA")

    # 6) Displaying Performance Parameters

    total_time = getTimePerformance(start, end, extra)

    residue_percentage = getResiduePercentage(no_of_records, residue_dict)

    diversity_percentage = getDiversityPerc(
        new_original_table, no_of_records, K, verbose=False)

    displayPerformance(no_of_records, no_of_unique_values_for_senstive_attribute, K,
                       sensitive_attribute, total_time, residue_percentage, diversity_percentage, algo)

    # 7) Converting to Pandas Dataframe
    masked_df, columns = NestedDictionaryToDataFrame(masked_microdata)

    displayDF(masked_df, columns)

    # 8) Returning the Performance Parameters values for the Graph Plotting

    return no_of_records, K, total_time, residue_percentage, diversity_percentage


# Plotting Graphs Function
def plotGraph(X, Y, x_lab, y_lab, constant):

    fig, ax = plt.subplots(dpi=420)  # More Resolution

    # Unpacking
    x1, x2, x3, x4, x5 = X
    y1, y2, y3, y4, y5 = Y

    # Multi Line Chart
    ax.plot(x1, y1, color="Red", marker="+", label="Marital Status")
    ax.plot(x2, y2, color="Green", marker="+",
            label="Marital Semantic Tree (One)")
    ax.plot(x3, y3, color="Purple", marker="+",
            label="Marital Semantic Tree (Two)")
    ax.plot(x4, y4, color="Blue", marker="+", label="Relationship")
    ax.plot(x5, y5, color="Orange", marker="+", label="Disease Semantic Tree")

    # Labelling Axes & Title
    plt.xlabel(x_lab)
    plt.ylabel(y_lab)
    plt.title("{} v/s {} for {}".format(x_lab, y_lab, constant))

    # Removing Right and Top Borders of Graph
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Adding legend
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    fig.tight_layout()  # To prevent Overlapping

    plt.show()

    return


def PerformanceParametersGraph():
    """ Plots the Graph of various performance parameters by keeping a parameter as constant
        Also displays the time taken to plot the graphs and
        the no. of times the main() function was called."""

    main_counter = 0

    """ K constant """

    t1 = time.time()

    K_constant = 3

    # Index 0,1,2,3,4 correspond to Algo 1,2,3,4,5
    records_list = [[], [], [], [], []]
    time_list = [[], [], [], [], []]
    residue_list = [[], [], [], [], []]
    diversity_list = [[], [], [], [], []]

    for records in range(25, 5026, 1000):   # 25 to 5025 in steps of 1000

        for algo in range(1, 5+1):  # 1,2,3,4,5

            no_of_records, K, total_time, residue_percentage, diversity_percentage = main(
                records, K_constant, algo)

            records_list[algo-1].append(no_of_records)
            time_list[algo-1].append(total_time)
            residue_list[algo-1].append(residue_percentage)
            diversity_list[algo-1].append(diversity_percentage)

            main_counter += 1

    # Records v/s Resdiue
    plotGraph(records_list, residue_list, "Records", "Residue %",
              "K = {}".format(K_constant))

    # Records v/s Time
    plotGraph(records_list, time_list, "Records", "Time (ms)",
              "K = {}".format(K_constant))

    # Records v/s Diversity
    plotGraph(records_list, diversity_list, "Records", "Diversity",
              "K = {}".format(K_constant))

    """ No. of records constant """

    records_constant = 5000

    time_list = [[], [], [], [], []]
    residue_list = [[], [], [], [], []]
    K_list = [[], [], [], [], []]
    diversity_list = [[], [], [], [], []]

    for K_val in range(1, 8+1):  # 1 to 8

        for algo in range(1, 5+1):  # 1,2,3,4,5

            no_of_records, K, total_time, residue_percentage, diversity_percentage = main(
                records_constant, K_val, algo)

            time_list[algo-1].append(total_time)
            residue_list[algo-1].append(residue_percentage)
            K_list[algo-1].append(K)
            diversity_list[algo-1].append(diversity_percentage)

            main_counter += 1

    # K v/s Residue
    plotGraph(K_list, residue_list, "K", "Residue %",
              "Records = {}".format(records_constant))

    # K v/s Time
    plotGraph(K_list, time_list, "K", "Time (ms)",
              "Records = {}".format(records_constant))

    # K v/s Diversity
    plotGraph(K_list, diversity_list, "K", "Diversity",
              "Records = {}".format(records_constant))

    t2 = time.time()

    t = round(t2 - t1)

    print("Graph Plotting Time = {} min, {} s".format(t//60, t % 60))
    print("main(): called {} times.".format(main_counter))

    return


def plotCompare(X, Y, x_lab, y_lab, constant):

    fig, ax = plt.subplots(dpi=420)  # More Resolution

    # Unpacking
    x1, x2 = X
    y1, y2 = Y

    # Multi Line Chart
    ax.plot(x1, y1, color="Blue", marker="+", label="Incremental Diversity")
    ax.plot(x2, y2, color="Green", marker="+", label="l,e diversity")

    # Labelling Axes & Title
    plt.xlabel(x_lab)
    plt.ylabel(y_lab)
    plt.title("{} v/s {} for {}".format(x_lab, y_lab, constant))

    # Removing Right and Top Borders of Graph
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Adding legend
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    fig.tight_layout()  # To prevent Overlapping

    plt.show()

    return


def ComparisonGraph():
    """ Plots the Graph of various performance parameters by keeping a parameter as constant
        Also displays the time taken to plot the graphs and
        the no. of times the main() function was called."""

    main_counter = 0

    """ K constant """

    t1 = time.time()

    K_constant = 3

    records_list = [[], []]   # Index 0,1 is Algo 5, -100
    time_list = [[], []]
    residue_list = [[], []]
    diversity_list = [[], []]

    for records in range(25, 5026, 1000):   # 25 to 5025 in steps of 1000

        for algo in [5, -100]:

            no_of_records, K, total_time, residue_percentage, diversity_percentage = main(
                records, K_constant, algo)

            ind = int(algo < 0)

            records_list[ind].append(no_of_records)
            time_list[ind].append(total_time)
            residue_list[ind].append(residue_percentage)
            diversity_list[ind].append(diversity_percentage)

            main_counter += 1

    # Records v/s Resdiue
    plotCompare(records_list, residue_list, "Records", "Residue %",
                "K = {}".format(K_constant))

    # Records v/s Time
    plotCompare(records_list, time_list, "Records", "Time (ms)",
                "K = {}".format(K_constant))

    # Records v/s Diversity
    plotCompare(records_list, diversity_list, "Records", "Diversity",
                "K = {}".format(K_constant))

    """ No. of records constant """

    records_constant = 5000

    time_list = [[], []]
    residue_list = [[], []]
    K_list = [[], []]
    diversity_list = [[], []]

    for K_val in range(1, 8+1):  # 1 to 8

        for algo in [5, -100]:

            no_of_records, K, total_time, residue_percentage, diversity_percentage = main(
                records_constant, K_val, algo)

            ind = int(algo < 0)

            time_list[ind].append(total_time)
            residue_list[ind].append(residue_percentage)
            K_list[ind].append(K)
            diversity_list[ind].append(diversity_percentage)

            main_counter += 1

    # K v/s Residue
    plotCompare(K_list, residue_list, "K", "Residue %",
                "Records = {}".format(records_constant))

    # K v/s Time
    plotCompare(K_list, time_list, "K", "Time (ms)",
                "Records = {}".format(records_constant))

    # K v/s Diversity
    plotCompare(K_list, diversity_list, "K", "Diversity",
                "Records = {}".format(records_constant))

    t2 = time.time()

    t = round(t2 - t1)

    print("Graph Plotting Time = {} min, {} s".format(t//60, t % 60))
    print("main(): called {} times.".format(main_counter))

    return


# Top Level Statements

# TWO MODES:

    # 1: Run Code for Specific Values of no_of_records, k, algorithm chosen
    # 2: Plot Performance Parameters Graph of Three Algorithms


print("Enter Code Mode:")
print("1) Test for a Specific Case")
print("2) Plot Graphs")
print("3) Our Algo v/s Paper Algo")
mode = int(input("Enter Mode: "))

if mode == 1:

    no_of_records = int(input("Enter no. of records: "))
    K = int(input("Enter k: "))
    print("""\nFive Algorithms can be chosen:
    1) Marital Status present only once
    2) Marital Status Semantic Tree only One Count
    3) Marital Status Semantic Tree with Two Count
    4) Relationship present only once
    5) Disease Semantic Tree""")
    algo_chosen = int(input("Enter algo no: "))

    no_of_records, K, total_time, residue_percentage, diversity_percentage = main(
        no_of_records, K, algo_chosen, True)

elif mode == 2:

    PerformanceParametersGraph()

elif mode == 3:

    ComparisonGraph()
