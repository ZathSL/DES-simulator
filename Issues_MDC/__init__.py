import warnings
import numpy as np
import pandas as pd
import scipy.stats as st
from scipy.stats._continuous_distns import _distn_names
import matplotlib.pyplot as plt
import matplotlib
import csv

matplotlib.rcParams['figure.figsize'] = (16.0, 12.0)
matplotlib.style.use('ggplot')


def get_dataset():
    file = open('../dataset/Dataset_SDO_Regione_Lombardia.csv')
    csvreader = csv.reader(file)
    filter_Issues_MDC(csvreader)


def filter_Issues_MDC(csvreader):
    data = {}
    for row in csvreader:
        if row[16] != 'DESCRIZIONE MDC':
            if not row[16] in data:
                data[row[16]] = 0
            else:
                data[row[16]] = data[row[16]]+1
    temp = list(data.values())
    plot_data(data, np.mean(temp), np.var(temp))


def best_fit_distribution(data, ax):
    print("Model data by finding best fit distribution to data")
    # Get bar diagram of original data
    #y = plt.bar(range(len(data)), list(data.values()), tick_label=list(data.keys()))
    #y, x = np.histogram(list(data.values()), bins = list(data.keys()))
    #x = (x + np.roll(x, -1))[:-1] / 2.0
    y = np.array(list(data.values()))
    x = np.array(list(data.keys()))
    print(y,x)
    # Best holders
    best_distributions = []

    # Estimate distribution parameters from data
    for ii, distribution in enumerate([d for d in _distn_names if not d in ['levy_stable', 'studentized_range']]):
        print("{:>3} / {:<3}: {}".format(ii + 1, len(_distn_names), distribution))
        distribution = getattr(st, distribution)

        # Try to fit the distribution
        try:
            # Ignore warnings from data that can't be fit
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore')

                # fit dist to data
                params = distribution.fit(data)

                # Separate parts of parameter
                arg = params[:-2]
                loc = params[-2]
                scale = params[-1]

                # Calculate fitted PDF and error with fir in distribution
                pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)
                sse = np.sum(np.power(y - pdf, 2.0))

                # if axis pass in add to plot
                try:
                    if ax:
                        pd.Series(pdf, x).plot(ax=ax)
                except Exception:
                    pass

                # identify if this distribution is better
                best_distributions.append((distribution, params, sse))

        except Exception:
            pass
    print(best_distributions)
    return sorted(best_distributions, key=lambda x: x[2])


def make_pdf(dist, params, size=10000):
    print("Generate distribution's Probability Distribution Function")

    # Separate parts of parameters
    arg = params[:-2]
    loc = params[-2]
    scale = params[-1]

    # Get sane start and end points of distribution
    start = dist.ppf(0.01, *arg, loc=loc, scale=scale) if arg else dist.ppf(0.01, loc=loc, scale=scale)
    end = dist.ppf(0.99, *arg, loc=loc, scale=scale) if arg else dist.ppf(0.99, loc=loc, scale=scale)

    # Build PDF and turn into pandas Series
    x = np.linspace(start, end, size)
    y = dist.pdf(x, loc=loc, scale=scale, *arg)
    pdf = pd.Series(y, x)

    return pdf


def plot_data(data, mean, var):
    # Plot for comparison
    plt.figure(figsize=(12, 8))
    code = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
            '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
            '21', '22', '23', '24', '25', 'PR', 'NA']
    print(data)
    df = pd.DataFrame.from_dict([data])
    ax = df.plot.bar()
    ax.set_yscale('log')
    # Save plot limits
    dataYLim = ax.get_ylim()

    # Find best fit distribution
    best_distributions = best_fit_distribution(data, ax)
    best_dist = best_distributions[0]

    # Update plots
    ax.set_ylim(dataYLim)
    ax.set_title('Fitted distribution')
    ax.set_xlabel('Issues')
    ax.set_ylabel('Frequency')

    # Make PDF with best params
    pdf = make_pdf(best_dist[0], best_dist[1])

    # Display
    plt.figure(figsize=(12, 8))
    ax = pdf.plot(lw=2, label='PDF', legend=True)
    ax.set_yscale('log')
    df.plot.bar()
    param_names = (best_dist[0].shapes + ', loc, scale').split(', ') if best_dist[0].shapes else ['loc', 'scale']
    param_str = ', '.join(['{}={:0.2f}'.format(k, v) for k, v in zip(param_names, best_dist[1])])
    dist_str = '{}({})'.format(best_dist[0].name, param_str)

    ax.set_title('Best distribution (mu=' + str(mean) + ', var=' + str(var) + ') \n' + dist_str)
    ax.set_xlabel('Issues MDC')
    ax.set_ylabel('Frequency')
    plt.savefig('IssuesMDCDistributeLOGLOG.jpg')

    # Display2
    plt.figure(figsize=(12, 8))
    ax = pdf.plot(lw=2, label='PDF', legend=True)
    ax.set_yscale('log')
    df.plot.bar()
    param_names = (best_dist[0].shapes + ', loc, scale').split(', ') if best_dist[0].shapes else ['loc', 'scale']
    param_str = ', '.join(['{}={:0.2f}'.format(k, v) for k, v in zip(param_names, best_dist[1])])
    dist_str = '{}({})'.format(best_dist[0].name, param_str)

    ax.set_title('Best distribution (mu=' + str(mean) + ', var=' + str(var) + ') \n' + dist_str)
    ax.set_xlabel('Issues MDC')
    ax.set_ylabel('Frequency')
    plt.savefig('IssuesMDCDistributeLOG.jpg')


def main():
    get_dataset()


if __name__ == '__main__':
    main()
