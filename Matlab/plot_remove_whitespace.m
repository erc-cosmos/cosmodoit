function plot_remove_whitespace(ax, DH, L, L0, H0, d)
% plot_remove_whitespace(ax, DH, L, L0, H0, d)
% Remove whitespace from vertical subplots
% ax : figure axes object
% DH : Vertical space between subplots (default=0.05)
% L  : Distance between the right and left inner edges of the figure (default=0.85)
% L0 : Start of the left edge of the subplot (default=0.1)
% H0 : Bottom start position of the last subplot (default=0.1)
% d  : Proportion of each subplot's original height (default=1.0)

if nargin<2
    DH = 0.05;
end
if nargin<3
    L=0.85;
end
if nargin<4
    L0 = 0.1;
end
if nargin<5
    H0=0.1;
end
if nargin<6
    d  = 1.0;
end

K = length(ax);
pos = zeros(K, 4);
for k=1:K
    pos(k,:) = get( ax(k), 'Position' );
end

H(1:K)=pos(1:K,4)*d;
Ki = fliplr(1:K);

for k=1:K
    idx = Ki(k);
    if k==1
        h = 0;
    else
        h = sum(H(idx+1:K));
    end
    set(ax(idx),'position',[L0 H0+h+DH*(k-1) L H(idx)]); % [left bottom width height]
end

end

